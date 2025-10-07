import asyncio
import logging
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..clients.ai_clients import gemini_client 

logger = logging.getLogger(__name__)

class BlogWritingAgent:
    """
    Blog Writing Agent - Generates complete blog content based on strategy data.
    Now supports both single-prompt and section-by-section generation modes with strict word count control.
    """
    
    def __init__(self, use_section_generation: bool = True):
        self.use_section_generation = use_section_generation
        
        # NEW: Word count configuration for strict control
        self.target_word_range = (2800, 3000)  # min, max words
        self.section_buffer_factor = 0.9  # Aim for 90% of target to account for AI variance
        self.allowed_word_variance = 0.1  # 10% variance per section

    # Consolidated prompt template for single-generation mode (backward compatible)
    BLOG_WRITING_PROMPT_TEMPLATE = """
You are a professional AI content writer. Generate a high-quality blog article in **{language}** based on comprehensive research.

# TOPIC & CONTEXT
Primary Topic: {topic}
Target Keyword: {target_keyword}
Search Intent: {search_intent}

# CORE REQUIREMENTS
- Language: Write entirely in **{language}**
- Word count: Target {word_count} words (±20%)
- REQUIRED: The article must contain between {min_word_count} and {max_word_count} words.
- If your draft is shorter, expand with detailed examples, case studies, and actionable insights.
- If your draft is longer, trim unnecessary repetition.
- At the end of your response, explicitly return the total word_count field (count your words).
- Tone: {tone} (professional, engaging, SEO-friendly)
- Structure: Follow the provided outline
- Accuracy: Factual, coherent, no hallucinations
- Citations: Include [citation] placeholders for factual claims

# RESEARCH INSIGHTS
## Competitor Analysis
{competitor_analysis}

## User Questions to Address
{common_questions}

## SEO Keywords to Include Naturally
{semantic_keywords}

## Content Opportunities
{content_gaps}

# ARTICLE OUTLINE
{outline}

# OUTPUT FORMAT
Return JSON with:
{{
  "title": "Engaging Article Title",
  "content": "Full article HTML with proper heading structure",
  "meta_description": "Compelling SEO meta description (150-160 chars)",
  "keywords": ["primary", "secondary", "keywords"],
  "word_count": 2500,
  "sections": [
    {{
      "heading": "Section Heading",
      "content": "Section content with proper formatting",
      "word_count": 500,
      "keywords_included": ["keyword1", "keyword2"]
    }}
  ],
  "citations_needed": [
    {{
      "claim": "Specific factual claim that needs verification",
      "context": "Surrounding sentence context"
    }}
  ]
}}
"""

    # UPDATED: Section-wise generation template with strict word count enforcement
    SECTION_WRITING_PROMPT_TEMPLATE = """
You are writing section #{section_number} of a blog article: "{section_heading}"

# CONTEXT
Overall Topic: {topic}
Target Keyword: {target_keyword}
Previous Section: {previous_section_content}

# STRICT WORD COUNT REQUIREMENT
- REQUIRED: This section must contain between {min_allowed} and {max_allowed} words.
- If it falls short, add more depth with research, examples, or practical advice.
- At the end of the JSON, include an accurate "word_count" field.
- If you need to go slightly under, that's acceptable
- Count your words carefully before responding

# SECTION-SPECIFIC GUIDELINES
- Continue naturally from the previous section
- Focus specifically on: {section_heading}
- Tone: {tone}
- Include relevant keywords: {section_keywords}

# RESEARCH CONTEXT
User Questions to Address: {common_questions}
Content Gaps to Fill: {content_gaps}

# OUTPUT FORMAT
Return JSON with:
{{
  "heading": "{section_heading}",
  "content": "Well-written section content (strictly {section_word_count} ±10% words)",
  "word_count": {section_word_count},  // MUST be close to target
  "keywords_used": ["keyword1", "keyword2"],
  "transition_sentence": "Sentence that connects to next section"
}}

# WORD COUNT ENFORCEMENT
- Be concise and focused
- Prioritize key information
- Avoid unnecessary elaboration
- Count your words before finalizing
"""

    async def generate_blog_draft(self, content_strategy: Dict[str, Any], 
                                tone: str = "professional", task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a complete blog draft - uses new section-wise generation or falls back to single-prompt.
        Maintains FULL backward compatibility with existing code.
        """
        try:
            if self.use_section_generation:
                # NEW: Section-by-section generation with word count control
                result = await self._generate_section_wise(content_strategy, tone, task_id)
            else:
                # ORIGINAL: Single-prompt generation (backward compatible)
                result = await self._generate_single_prompt(content_strategy, tone, task_id)
            
            # Ensure backward compatibility - same return structure
            validated_content = self._validate_and_enhance_content(result, content_strategy)
            citations_needed = self._extract_citation_needs(validated_content["content"])
            validated_content = await self.optimize_content(validated_content, seo_guidelines=None)
            
            # NEW: Final word count validation
            final_word_count = validated_content.get("word_count", 0)
            min_target, max_target = self.target_word_range
            if final_word_count < min_target or final_word_count > max_target:
                logger.warning(f"Final word count {final_word_count} outside target range {min_target}-{max_target}")
            
            within_range = min_target <= final_word_count <= max_target

            return {
                **validated_content,
                "citations_needed": citations_needed,
                "strategy_incorporated": True,
                "status": "draft_complete",
            }
                
        except Exception as e:
            logger.error(f"Blog writing failed: {str(e)}")
            return self._generate_fallback_draft(content_strategy, tone)

    # UPDATED: Section-wise generation with word count control
    async def _generate_section_wise(self, content_strategy: Dict, tone: str, task_id: Optional[str] = None) -> Dict:
        """Generate blog content section by section with strict word count control."""
        outline = content_strategy.get("outline", {})
        sections = outline.get("structure", [])
        
        if not sections:
            logger.warning("No sections in outline, falling back to single-prompt")
            return await self._generate_single_prompt(content_strategy, tone, task_id)
        
        # NEW: Calculate target word count per section
        target_total = sum(self.target_word_range) / 2  # Average of range
        adjusted_target = target_total * self.section_buffer_factor  # 90% buffer
        section_targets = self._calculate_section_word_targets(sections, adjusted_target)

        # ----> APPLY EXPANSION FACTOR HERE
        EXPANSION_FACTOR = 1.1  # +10% to expand sections
        section_targets = [int(t * EXPANSION_FACTOR) for t in section_targets]

                
        generated_sections = []
        previous_content = ""
        total_actual_words = 0
        
        for i, section in enumerate(sections):
            logger.info(f"Generating section {i+1}/{len(sections)}: {section.get('heading', 'Unknown')}")
            
            section_content = await self._generate_section(
                section=section,
                section_number=i+1,
                content_strategy=content_strategy,
                tone=tone,
                previous_content=previous_content,
                target_word_count=section_targets[i],  # NEW: Pass specific word count
                task_id=task_id
            )
            
            generated_sections.append(section_content)
            previous_content = section_content.get("content", "")
            total_actual_words += section_content.get("word_count", 0)
            
            # NEW: Log progress towards word count goal
            logger.info(f"Section {i+1} word count: {section_content.get('word_count', 0)} (target: {section_targets[i]})")
            logger.info(f"Total so far: {total_actual_words} / {target_total}")
            
            # Small delay between sections to avoid rate limiting
            if i < len(sections) - 1:
                await asyncio.sleep(1)
        
        # NEW: Final word count validation and adjustment
        return self._combine_and_adjust_sections(generated_sections, content_strategy, total_actual_words)

    def _calculate_section_word_targets(self, sections: List[Dict], total_target: int) -> List[int]:
        """Calculate word count targets for each section based on their estimated lengths."""
        total_estimated = sum(section.get("estimated_length", 400) for section in sections)
        
        if total_estimated == 0:
            # Fallback: equal distribution
            section_count = len(sections)
            return [total_target // section_count] * section_count
        
        # Distribute words proportionally to estimated lengths
        targets = []
        for section in sections:
            proportion = section.get("estimated_length", 400) / total_estimated
            targets.append(int(total_target * proportion))
        
        # Ensure total matches target (adjust for rounding)
        total_assigned = sum(targets)
        if total_assigned != total_target:
            difference = total_target - total_assigned
            # Distribute difference to largest section
            if targets:
                max_index = targets.index(max(targets))
                targets[max_index] += difference
        
        return targets

    # UPDATED: Section generation with word count validation
    async def _generate_section(self, section: Dict, section_number: int, content_strategy: Dict, 
                              tone: str, previous_content: str, target_word_count: int, 
                              task_id: Optional[str] = None) -> Dict:
        """Generate a single section with word count validation."""
        prompt = self.SECTION_WRITING_PROMPT_TEMPLATE.format(
            section_number=section_number,
            section_heading=section.get("heading", ""),
            topic=content_strategy.get("topic", ""),
            target_keyword=content_strategy.get("target_keyword", ""),
            previous_section_content=previous_content[-500:] if previous_content else "This is the first section.",
            section_word_count=target_word_count,  # Use calculated target
            tone=tone,
            section_keywords=", ".join(section.get("keywords", [])),
            common_questions=self._format_list(
                content_strategy.get("research_data", {}).get("common_questions", [])[:3], 
                "question"
            ),
            content_gaps=self._format_list(
                content_strategy.get("research_data", {}).get("content_gaps", [])[:2], 
                "gap"
            )
        )
        
        try:
            section_data = await gemini_client.generate_structured(prompt=prompt) 
            
            # VALIDATE WORD COUNT
            actual_words = section_data.get("word_count", 0)
            allowed_variance = target_word_count * self.allowed_word_variance
            min_allowed = target_word_count - allowed_variance
            max_allowed = target_word_count + allowed_variance
            
            if actual_words < min_allowed or actual_words > max_allowed:
                logger.warning(f"Section {section_number} word count {actual_words} outside range {min_allowed}-{max_allowed}")
            
            # Ensure section has required fields
            section_data.setdefault("heading", section.get("heading", ""))
            section_data.setdefault("content", "")
            section_data.setdefault("word_count", actual_words)
            
            return section_data
            
        except Exception as e:
            logger.error(f"Section generation failed: {str(e)}")
            return self._generate_fallback_section(section, content_strategy, target_word_count)

    def _combine_and_adjust_sections(self, sections: List[Dict], content_strategy: Dict, total_words: int) -> Dict:
        """Combine sections and adjust if word count is outside target range."""
        min_target, max_target = self.target_word_range
        
        if total_words > max_target:
            logger.warning(f"Blog too long ({total_words} words), trimming content")
            sections = self._trim_sections(sections, total_words - max_target)
        
        return self._combine_sections(sections, content_strategy)

    def _expand_sections(self, sections: List[Dict], words_needed: int) -> List[Dict]:
        """Expand sections to meet minimum word count."""
        if not sections or words_needed <= 0:
            return sections
        
        # Add words proportionally to existing sections
        total_current = sum(section.get("word_count", 0) for section in sections)
        if total_current == 0:
            return sections
            
        expansion_factor = 1 + (words_needed / total_current)
        
        expanded_sections = []
        for section in sections:
            current_words = section.get("word_count", 0)
            target_words = int(current_words * expansion_factor)
            
            # Mark for expansion (actual expansion would need re-generation)
            section["needs_expansion"] = target_words - current_words
            expanded_sections.append(section)
        
        return expanded_sections

    def _trim_sections(self, sections: List[Dict], words_to_remove: int) -> List[Dict]:
        """Trim sections to meet maximum word count."""
        if not sections or words_to_remove <= 0:
            return sections
        
        # Remove words proportionally from existing sections
        total_current = sum(section.get("word_count", 0) for section in sections)
        if total_current == 0:
            return sections
            
        reduction_factor = 1 - (words_to_remove / total_current)
        
        trimmed_sections = []
        for section in sections:
            current_words = section.get("word_count", 0)
            target_words = max(100, int(current_words * reduction_factor))  # Keep sections meaningful
            
            # Mark for trimming
            section["needs_trimming"] = current_words - target_words
            trimmed_sections.append(section)
        
        return trimmed_sections

    def _combine_sections(self, sections: List[Dict], content_strategy: Dict) -> Dict:
        """Combine generated sections into a complete blog draft."""
        full_content = ""
        total_word_count = 0
        
        for i, section in enumerate(sections):
            heading_level = "h1" if i == 0 else "h2"
            full_content += f'<{heading_level}>{section["heading"]}</{heading_level}>\n'
            full_content += f'{section["content"]}\n\n'
            total_word_count += section.get("word_count", 0)
        
        # Create the final blog structure (maintaining backward compatibility)
        return {
            "title": content_strategy.get("outline", {}).get("title", "Generated Blog Post"),
            "content": full_content.strip(),
            "meta_description": content_strategy.get("outline", {}).get("meta_description", ""),
            "keywords": content_strategy.get("semantic_keywords", []),
            "word_count": total_word_count,
            "sections": sections  # NEW: Now contains detailed section data
        }

    # ORIGINAL: Single-prompt generation (maintained for backward compatibility)
    async def _generate_single_prompt(self, content_strategy: Dict, tone: str, task_id: Optional[str] = None) -> Dict:
        """Original single-prompt generation method - maintained for backward compatibility."""
        prompt = self._build_writing_prompt(content_strategy, tone)
        content = await gemini_client.generate_structured(prompt=prompt)   
        return content

    # ALL ORIGINAL METHODS MAINTAINED FOR BACKWARD COMPATIBILITY
    def _build_writing_prompt(self, content_strategy: Dict, tone: str) -> str:
        """Build comprehensive writing prompt with all strategy data."""
        topic = content_strategy.get("topic", "")
        target_keyword = content_strategy.get("target_keyword", "")
        search_intent = content_strategy.get("search_intent", "informational")
        language = "en"
        
        competitor_analysis = content_strategy.get("competitor_analysis", {})
        common_questions = content_strategy.get("research_data", {}).get("common_questions", [])
        semantic_keywords = content_strategy.get("research_data", {}).get("semantic_keywords", [])
        content_gaps = content_strategy.get("research_data", {}).get("content_gaps", [])
        outline = content_strategy.get("outline", {})
        
        word_count = outline.get("word_count_target", 2500)
        
        return self.BLOG_WRITING_PROMPT_TEMPLATE.format(
            topic=topic,
            target_keyword=target_keyword,
            search_intent=search_intent,
            language=language,
            word_count=word_count,
            tone=tone,
            competitor_analysis=self._format_competitor_analysis(competitor_analysis),
            common_questions=self._format_list(common_questions[:8], "question"),
            semantic_keywords=self._format_list(semantic_keywords[:15], "keyword"),
            content_gaps=self._format_list(content_gaps[:5], "gap"),
            outline=json.dumps(outline, ensure_ascii=False, indent=2)
        )

    def _format_competitor_analysis(self, analysis: Dict) -> str:
        """Format competitor analysis for prompt."""
        if not analysis:
            return "No specific competitor analysis available."
        
        formatted = []
        competitors = analysis.get("top_competitors", [])
        
        for comp in competitors[:3]:
            name = comp.get("name", "Unknown competitor")
            strengths = comp.get("strengths", [])
            weaknesses = comp.get("weaknesses", [])
            
            comp_text = f"{name}: "
            if strengths:
                comp_text += f"Strengths: {', '.join(strengths[:2])}. "
            if weaknesses:
                comp_text += f"Weaknesses: {', '.join(weaknesses[:2])}"
            
            formatted.append(comp_text)
        
        return "\n".join(formatted)

    def _format_list(self, items: List, item_type: str) -> str:
        """Format a list of items for the prompt with null-safety."""
        if not items:
            return f"No {item_type}s identified."
        
        # FILTER OUT None VALUES
        valid_items = [item for item in items if item is not None]
        
        if not valid_items:
            return f"No valid {item_type}s identified."
        
        return "\n".join([f"- {item}" for item in valid_items[:10]])

    def _validate_and_enhance_content(self, content: Dict, strategy: Dict) -> Dict:
        """Validate and enhance the generated content."""
        required_fields = ["title", "content", "meta_description"]
        for field in required_fields:
            if field not in content:
                content[field] = self._generate_fallback_field(field, strategy)
        
        content["target_keyword"] = strategy.get("target_keyword")
        content["search_intent"] = strategy.get("search_intent")
        content["language"] = strategy.get("language", "en")
        content["word_count"] = self._count_words(content.get("content", ""))
        
        if "keywords" not in content:
            semantic_keywords = strategy.get("research_data", {}).get("semantic_keywords", [])
            content["keywords"] = [strategy.get("target_keyword")] + semantic_keywords[:4]
        
        return content

    def _extract_citation_needs(self, content: str) -> List[Dict]:
        """Extract claims that need citation from content."""
        citations_needed = []
        citation_pattern = r'\[citation\](.*?)(?=\[citation\]|$)'
        matches = re.finditer(citation_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            claim = match.group(1).strip()
            if claim and len(claim) > 10:
                start = max(0, match.start() - 100)
                end = min(len(content), match.end() + 100)
                context = content[start:end]
                
                citations_needed.append({
                    "claim": claim,
                    "context": context,
                    "original_marker": f"[citation]{claim}"
                })
        
        return citations_needed

    def _count_words(self, text: str) -> int:
        """Count words in text."""
        if not text:
            return 0
        return len(re.findall(r'\w+', text))

    def _generate_fallback_field(self, field: str, strategy: Dict) -> str:
        """Generate fallback content for missing fields."""
        topic = strategy.get("topic", "")
        keyword = strategy.get("target_keyword", "")
        
        if field == "title":
            return f"Comprehensive Guide to {topic}"
        elif field == "meta_description":
            return f"Learn everything about {topic} with this comprehensive guide. {keyword} explained in detail."
        elif field == "content":
            return f"<h1>Comprehensive Guide to {topic}</h1><p>This article provides a detailed overview of {topic}.</p>"
        return ""

    # UPDATED: Fallback section with target word count
    def _generate_fallback_section(self, section: Dict, content_strategy: Dict, target_word_count: int) -> Dict:
        """Generate fallback section content with target word count."""
        topic = content_strategy.get("topic", "the topic")
        
        # Create content that approximates the target word count
        base_content = f"<p>This section discusses {section.get('heading', 'the topic')}. [citation]Specific details need verification[citation].</p>"
        base_words = self._count_words(base_content)
        
        # Add placeholder content to reach target
        additional_content = ""
        if base_words < target_word_count:
            words_needed = target_word_count - base_words
            # Add placeholder sentences (approx 15 words each)
            sentences_needed = max(1, words_needed // 15)
            for _ in range(sentences_needed):
                additional_content += f" <p>Additional information about {section.get('heading', 'this topic')} would be covered here. [citation]More details require verification[citation].</p>"
        
        full_content = base_content + additional_content
        
        return {
            "heading": section.get("heading", "Section"),
            "content": full_content,
            "word_count": self._count_words(full_content),
            "keywords_used": section.get("keywords", []),
            "is_fallback": True
        }

    def _generate_fallback_draft(self, content_strategy: Dict, tone: str) -> Dict:
        """Generate fallback draft when AI fails completely."""
        topic = content_strategy.get("topic", "the topic")
        keyword = content_strategy.get("target_keyword", "")
        
        return {
            "title": f"Comprehensive Guide to {topic}",
            "content": f"""
            <h1>Comprehensive Guide to {topic}</h1>
            <p>This article provides a detailed overview of {topic} and its importance.</p>
            
            <h2>What is {topic}?</h2>
            <p>{topic} refers to [citation]the specific concept or definition that needs verification[citation].</p>
            
            <h2>Key Benefits</h2>
            <p>The main advantages of {topic} include [citation]specific benefits that need verification[citation].</p>
            
            <h2>How to Get Started</h2>
            <p>To begin with {topic}, you should [citation]specific steps or recommendations[citation].</p>
            
            <h2>Conclusion</h2>
            <p>{topic} offers significant value for [citation]target audience or use case[citation].</p>
            """,
            "meta_description": f"Learn everything about {topic} with this comprehensive guide. {keyword} explained in detail.",
            "keywords": [keyword] + content_strategy.get("research_data", {}).get("semantic_keywords", [])[:3],
            "word_count": 800,
            "citations_needed": [
                {
                    "claim": f"the specific concept or definition of {topic}",
                    "context": f"What is {topic}? {topic} refers to [citation]the specific concept or definition that needs verification[citation]."
                }
            ],
            "strategy_incorporated": True,
            "status": "fallback_draft", 
        }

    async def optimize_content(self, draft: Dict, seo_guidelines: Optional[Dict] = None) -> Dict:
        """
        Optimize the generated content based on SEO guidelines.
        Maintains backward compatibility with existing calls.
        """
        optimized = draft.copy()

        if seo_guidelines:
            target_keyword = seo_guidelines.get("target_keyword")
            if target_keyword:
                optimized["title"] = f"{optimized.get('title', target_keyword)} | {target_keyword}"
                optimized["meta_description"] = f"{optimized.get('meta_description', '')} | Learn about {target_keyword}."

            semantic_keywords = seo_guidelines.get("semantic_keywords", [])
            for section in optimized.get("sections", []):
                section["keywords_used"] = list(set(section.get("keywords_used", []) + semantic_keywords))

            max_word_count = seo_guidelines.get("max_word_count")
            if max_word_count:
                optimized["word_count"] = min(optimized.get("word_count", max_word_count), max_word_count)

        optimized["seo_optimized"] = True
        optimized["seo_applied_at"] = datetime.now().isoformat()

        return optimized