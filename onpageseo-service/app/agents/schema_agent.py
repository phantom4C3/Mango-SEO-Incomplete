# onpageseo-service/app/agents/schema_agent.py
from typing import Dict, List, Optional
import logging
import json
import re
from shared_models.models import AgentType, AgentResult
from ..clients.ai_clients import gemini_client

logger = logging.getLogger(__name__)


class SchemaAgent:
    """AI agent for structured data schema generation and validation"""

    def __init__(self): 
        self.agent_type = AgentType.SCHEMA
        self.ai_client = gemini_client  # use shared Gemini client
        

    async def generate_schema(
        self,
        content: str,
        page_type: Optional[str] = None,
        existing_schema: Optional[List[Dict]] = None,
        analyzer_context: Optional[Dict] = None,
    ) -> AgentResult:
        """
        Generate and validate JSON-LD schema markup for content.
        Enhances existing schema, adds missing schema, ensures Rich Result eligibility.
        """
        try:
            schema_issues = []
            if analyzer_context:
                schema_issues = [
                    issue
                    for issue in analyzer_context.get("issues", [])
                    if "schema" in issue.get("type", "").lower()
                ]

            prompt = self._build_schema_prompt(
                content, page_type, existing_schema, schema_issues
            )

            response = await self.ai_client.generate_structured(
                prompt=prompt, 
            )

            schema_data = self._parse_and_validate_response(response)

            return AgentResult(
                agent_type=self.agent_type,
                input_data={
                    "content_length": len(content),
                    "page_type": page_type,
                    "existing_schema_count": len(existing_schema) if existing_schema else 0,
                    "analyzer_issues_count": len(schema_issues),
                },
                output_data=schema_data,
                processing_time=response.get("processing_time", 0),
                confidence_score=response.get("confidence", 0.85),
                cost_estimate=response.get("cost_estimate", 0.025),
                tokens_used=response.get("tokens_used"),
            )

        except Exception as e:
            logger.error(f"Schema generation failed: {str(e)}")
            return AgentResult(
                agent_type=self.agent_type,
                input_data={
                    "content_length": len(content),
                    "page_type": page_type,
                    "existing_schema_count": len(existing_schema) if existing_schema else 0,
                    "analyzer_issues_count": len(analyzer_context.get("issues", [])) if analyzer_context else 0,
                },
                output_data={},
                processing_time=0,
                confidence_score=0.0,
                cost_estimate=0,
                tokens_used=0,
                error=str(e),
            )

    def _build_schema_prompt(
        self,
        content: str,
        page_type: Optional[str],
        existing_schema: Optional[List[Dict]],
        schema_issues: List[Dict] = None,
    ) -> str:
        """Build prompt for schema generation with analyzer context and Rich Result requirements"""
        prompt = """
        Generate a valid JSON-LD structured data markup for the following page content.

        Content: {content}

        {issues_section}
        {page_type_section}
        {existing_schema_section}

        Requirements:
        1. Use appropriate schema.org types based on the content.
        2. If existing schema is provided, enhance and merge it.
        3. Add any missing schema types relevant to the content.
        4. Include required properties for Google Rich Results eligibility.
        5. Suggest FAQ or HowTo schema if applicable.
        6. Fix issues flagged in analyzer context.
        7. Follow Google's structured data guidelines.
        8. Return only valid JSON-LD, no explanations.
        """

        issues_section = ""
        if schema_issues:
            issues_text = "\n".join(
                [f"- {issue.get('message')}" for issue in schema_issues]
            )
            issues_section = f"Schema issues to address:\n{issues_text}\n\n"

        page_type_section = f"Page type: {page_type}\n" if page_type else ""

        existing_schema_section = ""
        if existing_schema:
            existing_schema_section = (
                f"Existing schema to enhance: {json.dumps(existing_schema[:2])}\n"
            )

        return prompt.format(
            content=content[:1500],
            issues_section=issues_section,
            page_type_section=page_type_section,
            existing_schema_section=existing_schema_section,
        )

    def _parse_and_validate_response(self, response: Dict) -> Dict:
        """Parse AI response into schema JSON and validate minimal rules"""
        try:
            schema_data = response if isinstance(response, dict) else {}

            if isinstance(schema_data, str):
                try:
                    schema_data = json.loads(schema_data)
                except json.JSONDecodeError:
                    schema_data = self._extract_json_from_text(schema_data)

            # Minimal validation inline (merged _validate_schema)
            validation_issues = []
            if not schema_data:
                validation_issues.append("Empty schema data")
            else:
                if "@type" not in schema_data:
                    validation_issues.append("Missing @type property")
                if "@context" not in schema_data:
                    validation_issues.append("Missing @context property")
                elif schema_data["@context"] != "https://schema.org":
                    validation_issues.append("Invalid @context, should be https://schema.org")

            return {
                "schema_json": schema_data,
                "schema_type": schema_data.get("@type", "Unknown"),
                "validation_issues": validation_issues,
                "rich_result_eligible": len(validation_issues) == 0,
            }

        except Exception as e:
            logger.error(f"Failed to parse schema response: {str(e)}")
            return {
                "schema_json": {},
                "schema_type": "Unknown",
                "validation_issues": ["Failed to parse schema response"],
                "rich_result_eligible": False,
            }

    def _extract_json_from_text(self, text: str) -> Dict:
        """Extract JSON from text response"""
        try:
            json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))

            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))

        except Exception as e:
            logger.warning(f"Failed to extract JSON from text: {str(e)}")
        return {}
