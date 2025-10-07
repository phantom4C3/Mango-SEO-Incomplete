# backend\src\services\pixel_service.py
import logging
from typing import Dict, Any, Optional, List
from uuid import UUID
import json
from datetime import datetime, timedelta

from ..clients.supabase_client import supabase_client  # async Supabase client
from ..core.config import settings 
from shared_models.models import PixelDeploymentPlan, AIRecommendation
from ..clients.redis_client import RedisCache



logger = logging.getLogger(__name__)


class PixelService: 

    async def generate_pixel_code(self, website_id: UUID, user_id: UUID, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate unique pixel code for a website"""
        pixel_id = self._generate_pixel_id(website_id, user_id)
        script_code = await self.generate_pixel_script(pixel_id)
        
        return {
            "pixel_id": pixel_id,
            "script_code": script_code,
            "instructions": self._get_installation_instructions()
        }
    
    async def get_optimizations(self, pixel_id: str, page_url: str) -> Dict[str, Any]:
        """
        Fetch active optimizations for pixel.js with caching.
        Always cleans results via _format_optimizations before returning.
        """
        cache_key = f"pixel:{pixel_id}:{page_url}"

        # Try cache first
        try:
            cached = await RedisCache.cache_get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Redis cache failed: {str(e)}")

        # Fetch from database
        try:
           # 1. Get url_id from latest pixel activity
            latest_activity = await supabase_client.fetch_one(
                "pixel_activity",
                {"pixel_id": pixel_id, "page_url": page_url},
                order={"col": "created_at", "desc": True}
            )
            if not latest_activity:
                return {}

            url_id = latest_activity["url_id"]

            # 2. Fetch recommendations by url_id instead of pixel_id/page_url
            res = await supabase_client.fetch_all(
                "ai_recommendations",
                filters=[
                    {"op": "eq", "col": "url_id", "val": url_id},
                    {"op": "eq", "col": "is_active", "val": True},
                    {"op": "eq", "col": "user_approved", "val": True},
                ],
                order={"col": "created_at", "desc": True},
                select="*",
            )


            if not res:
                return {}

            # ✅ Clean before returning
            formatted_optimizations = self._format_optimizations(res)

            # Add last updated timestamp
            formatted_optimizations["last_updated"] = datetime.utcnow().isoformat()

            # Cache result
            try:
                await RedisCache.cache_set(
                    cache_key, 
                    json.dumps(formatted_optimizations), 
                    ttl=300  # 5 min
                )
            except Exception as e:
                logger.warning(f"Failed to cache optimizations: {str(e)}")

            return formatted_optimizations

        except Exception as e:
            logger.error(f"Failed to fetch optimizations from DB: {str(e)}")
            return {}

    async def rollback_optimizations(self, url_id: UUID, version_id: Optional[str] = None) -> bool:
        """Rollback to a previous version of optimizations"""
        try:
            table_name = "deployment_plans"

            if version_id:
                # Rollback to specific version
                await supabase_client.update_table(
                    table_name=table_name,
                    filters={"id": version_id},
                    updates={"is_active": True, "updated_at": datetime.utcnow().isoformat()}
                )
            else:
                # Deactivate current active version
                await supabase_client.update_table(
                    table_name=table_name,
                    filters={"url_id": url_id, "is_active": True},
                    updates={"is_active": False, "updated_at": datetime.utcnow().isoformat()}
                )

                # Activate previous version if exists
                previous_versions = await supabase_client.fetch_all(
                    table_name,
                    filters=[{"op": "eq", "col": "url_id", "val": url_id}],
                    order={"col": "created_at", "desc": True}
                )

                if previous_versions and len(previous_versions) > 1:
                    prev_id = previous_versions[1]["id"]
                    await supabase_client.update_table(
                        table_name=table_name,
                        filters={"id": prev_id},
                        updates={"is_active": True, "updated_at": datetime.utcnow().isoformat()}
                    )
            # At the end of rollback_optimizations, before return True
            cache_key = f"pixel:{url_id}:*"
            await RedisCache.cache_delete_pattern(cache_key)

            await self._log_deployment_activity(
                str(url_id),
                "<page_url>",  # replace with actual page_url if available
                "rollback",
                details={"version_id": version_id}
            )

            return True

        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}")
            return False 
        
    async def get_pixel_status(self, pixel_id: str) -> Dict[str, Any]:
        """Get status and analytics for a pixel"""
        try:
            # 1. Fetch latest pixel activity to get the url_id
            latest_activity = await supabase_client.fetch_one(
                "pixel_activity",
                {"pixel_id": pixel_id},
                order={"col": "created_at", "desc": True}
            )
            if not latest_activity:
                raise Exception("Pixel activity not found")

            url_id = latest_activity["url_id"]

            # 2. Fetch page info
            pixel_data = await supabase_client.fetch_one(
                "page_seo_data",
                {"id": url_id}
            )

            if not pixel_data:
                raise Exception("Page data not found")

            # 3. Fetch AI recommendations for this page
            recommendations = await supabase_client.fetch_all(
                "ai_recommendations",
                filters=[{"op": "eq", "col": "url_id", "val": url_id}],
                order={"col": "created_at", "desc": True}
            )

            # 4. Fetch deployment activity
            deployments = await supabase_client.fetch_all(
                "deployment_plans",
                filters=[{"op": "eq", "col": "url_id", "val": url_id}]
            )

            total_activations = len(recommendations)
            total_deployments = len(deployments)
            last_seen = latest_activity["created_at"]

            return {
                "pixel_id": pixel_id,
                "is_active": True,
                "website_id": pixel_data.get("website_id"),
                "created_at": pixel_data.get("created_at"),
                "last_seen": last_seen,
                "stats": {
                    "total_activations": total_activations,
                    "total_deployments": total_deployments
                }
            }

        except Exception as e:
            logger.error(f"Failed to get pixel status: {str(e)}")
            raise
 

    
    def _generate_pixel_id(self, website_id: UUID, user_id: UUID) -> str:
        """Generate unique pixel ID"""
        import hashlib
        unique_string = f"{website_id}_{user_id}_{datetime.utcnow().timestamp()}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:16]
     
    def _get_installation_instructions(self) -> str:
        """Get pixel installation instructions"""
        return """
        Installation Instructions:
        1. Copy the entire script code below
        2. Paste it just before the </head> tag on your website
        3. For best results, install on all pages
        4. Changes will appear within 24 hours
        
        For CMS-specific instructions:
        - WordPress: Use a header plugin or theme editor
        - Shopify: Edit theme.liquid in the header section
        - Custom sites: Add to your template system
        """
    
    def _format_optimizations(self, deployed_recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Normalize and clean AI recommendations for pixel.js consumption.
        Filters out None/null/empty values and unknown types.
        """
        optimizations = {}

        for deployment in deployed_recommendations:
            rec = deployment.get("ai_recommendations", deployment)
            rec_type = rec.get("type")
            suggested = rec.get("suggested")

            # Skip if no suggestion or empty
            if suggested in (None, "", [], {}):
                continue

            # ✅ Only map known recommendation types
            if rec_type == "title_optimization":
                optimizations["title"] = suggested
            elif rec_type == "meta_description_optimization":
                optimizations["meta_description"] = suggested
            elif rec_type == "schema_markup":
                try:
                    optimizations["schema_markup"] = json.loads(suggested)
                except Exception:
                    optimizations["schema_markup"] = suggested
            elif rec_type == "faq_markup":
                optimizations["faq_markup"] = suggested
            elif rec_type == "image_alt_tags":
                optimizations["image_alt_tags"] = suggested
            else:
                # ❌ skip unknown types, do not include
                continue

        return optimizations

    
    async def generate_pixel_script(self, pixel_id: str) -> str:
        """
        Generate the pixel JS loader for a given pixel_id.
        This returns JS that fetches the JSON recs and applies them.
        """
        api_base_url = settings.PUBLIC_API_URL.rstrip("/")

        script = f"""
        (function() {{
            var siteId = "{pixel_id}";
            var url = encodeURIComponent(window.location.href);
            var apiUrl = "{api_base_url}/seo/pixel/deploy?pixel_id=" + siteId + "&url=" + url;

            fetch(apiUrl, {{ method: 'GET', headers: {{ 'Content-Type': 'application/json' }} }})
            .then(function(res) {{ return res.json(); }})
            .then(function(data) {{
                // 🚨 Add this check for empty optimizations
                if (!data.optimizations || Object.keys(data.optimizations).length === 0) {{
                    console.warn("No optimizations found for this page.");
                    return;
                }}

                applySEOptimizations(data.optimizations);
            }})
            .catch(function(err) {{ console.error("SEO Pixel error:", err); }});

            function applySEOptimizations(optimizations) {{
                if (optimizations.title) document.title = optimizations.title;

                if (optimizations.meta_description) {{
                    var meta = document.querySelector('meta[name="description"]');
                    if (!meta) {{
                        meta = document.createElement('meta');
                        meta.name = "description";
                        document.head.appendChild(meta);
                    }}
                    meta.content = optimizations.meta_description;
                }}

                if (optimizations.schema_markup) {{
                    try {{
                        var schema = document.createElement('script');
                        schema.type = "application/ld+json";
                        schema.text = JSON.stringify(optimizations.schema_markup);
                        document.head.appendChild(schema);
                    }} catch(e) {{
                        console.warn("Failed to apply schema_markup:", e);
                    }}
                }}

                if (optimizations.faq_markup) {{
                    // optionally inject FAQ structured data
                    try {{
                        var faq = document.createElement('script');
                        faq.type = "application/ld+json";
                        faq.text = JSON.stringify(optimizations.faq_markup);
                        document.head.appendChild(faq);
                    }} catch(e) {{
                        console.warn("Failed to apply FAQ markup:", e);
                    }}
                }}

                if (optimizations.image_alt_tags) {{
                    // update image alt attributes safely
                    Object.entries(optimizations.image_alt_tags).forEach(([imgSelector, altText]) => {{
                        try {{
                            var img = document.querySelector(imgSelector);
                            if (img) img.alt = altText;
                        }} catch(e) {{
                            console.warn("Failed to apply image alt tag:", e);
                        }}
                    }});
                }}
            }}
        }})();
        """
        return script


    async def get_pixel_activity(self, pixel_id: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Fetch pixel activity logs from DB"""
        try:
            response = await supabase_client.fetch_all(
                "pixel_activity",
                filters=[{"op": "eq", "col": "pixel_id", "val": pixel_id}],
                order={"col": "created_at", "desc": True},
                range=(offset, offset + limit - 1)
            )
            return {
                "pixel_id": pixel_id,
                "activities": response,
                "total": len(response)
            }
        except Exception as e:
            logger.error(f"Failed to fetch pixel activity: {str(e)}")
            return {"pixel_id": pixel_id, "activities": [], "total": 0, "error": str(e)}


    async def create_deployment_plan(
        self,
        url_id: str,
        recommendation_ids: List[str],
        optimization_level: str = "standard",
        task_id: Optional[str] = None,
        recommendations: Optional[List[AIRecommendation]] = None,
    ) -> Optional[PixelDeploymentPlan]:
        try:
            # 🔑 Cache key now unique per url_id/task_id + recommendation_ids
            ids_key = "-".join(sorted(recommendation_ids))
            cache_key = f"recommendations:{task_id or url_id}:{ids_key}"

            cached = await RedisCache.cache_get(cache_key)
            if cached:
                rows = json.loads(cached)
            else:
                filters = {"url_id": url_id}
                if task_id:
                    filters["task_id"] = task_id

                rows = await supabase_client.fetch_all(
                    "ai_recommendations", filters=filters, select="*"
                )

                # 🔑 Apply filtering BEFORE caching
                rows = [
                    r
                    for r in rows
                    if r["id"] in recommendation_ids and r.get("user_approved", False)
                ]

                await RedisCache.cache_set(cache_key, json.dumps(rows), ttl=300)

            if not rows:
                logger.error(
                    f"No recommendations found for URL ID: {url_id} with provided IDs"
                )
                return None

            recommendations = [AIRecommendation(**r) for r in rows]

            # Filter recommendations based on optimization level
            filtered_recommendations = self._filter_by_optimization_level(
                recommendations, optimization_level
            )

            if not filtered_recommendations:
                logger.warning(
                    f"No recommendations match optimization level: {optimization_level}"
                )
                return None
            
            # Convert recommendations into changes JSON
            changes = self._format_optimizations([{"ai_recommendations": r.dict()} for r in filtered_recommendations])

            # Create deployment plan
            deployment_plan = PixelDeploymentPlan(
                url_id=url_id,
                changes=changes,   # ✅ map AI recs → deployment changes
                rollback_strategy=self._create_rollback_strategy(filtered_recommendations),
                estimated_impact=sum(r.impact_score for r in filtered_recommendations)
                / len(filtered_recommendations),
                risk_level=self._calculate_risk_level(filtered_recommendations),
                dependencies=self._identify_dependencies(filtered_recommendations),
                required_approval=optimization_level == "aggressive",
                deployment_order=self._determine_deployment_order(filtered_recommendations),
                validation_rules=self._create_validation_rules(filtered_recommendations),
                created_at=datetime.now(),
            )

            # Store deployment plan
            plan_data = deployment_plan.dict()
            plan_data["created_at"] = deployment_plan.created_at.isoformat()

            await supabase_client.insert_into("deployment_plans", plan_data)

            return deployment_plan

        except Exception as e:
            logger.error(f"Failed to create deployment plan: {str(e)}")
            return None


    
    async def _deploy_via_pixel(self, pixel_id: str, page_url: str) -> bool:
        """
        Deploy via pixel.js - fetches active recommendations by url_id and logs the deployment.
        """
        try:
            # 1. Find the url_id from latest pixel activity
            latest_activity = await supabase_client.fetch_one(
                "pixel_activity",
                {"pixel_id": pixel_id, "page_url": page_url},
                order={"col": "created_at", "desc": True}
            )
            if not latest_activity:
                logger.warning(f"No pixel activity found for {pixel_id} / {page_url}")
                return False

            url_id = latest_activity["url_id"]

            # 2. Fetch active recommendations for this page
            recs = await supabase_client.fetch_all(
                "ai_recommendations",
                filters=[
                    {"op": "eq", "col": "url_id", "val": url_id},
                    {"op": "eq", "col": "user_approved", "val": True},
                ],
                order={"col": "created_at", "desc": True}
            )

            if not recs:
                logger.warning(f"No active recommendations found for pixel {pixel_id}, page {page_url}")
                return False

            # 3. Format optimizations for pixel.js
            optimizations = self._format_optimizations([{"ai_recommendations": r} for r in recs])

            # 4. Cache for pixel.js
            cache_key = f"pixel:{pixel_id}:{page_url}"
            await RedisCache.cache_set(cache_key, json.dumps(optimizations), ttl=300)

            # 5. Log deployment
            await self._log_deployment_activity(
                pixel_id,
                page_url,
                "pixel_js",
                details={"optimizations_applied": list(optimizations.keys())}
            )

            return True

        except Exception as e:
            logger.error(f"Pixel deployment failed for {pixel_id} / {page_url}: {str(e)}")
            return False



    
    async def _get_website_config(self, pixel_id: str) -> Optional[Dict[str, Any]]:
        """Get website-specific deployment configuration."""
        return await supabase_client.fetch_one(
            "website_configs", 
            {"pixel_id": pixel_id}
        ) 
 
    async def deploy_recommendations(
    self,
    task_id: str,
    recommendation_ids: list,
    optimization_level: str = "standard"
) -> dict:
        """
        Main orchestrator for pixel deployment.
        1. Fetch recommendations
        2. Create deployment plan
        3. Deploy via pixel
        4. Return status
        """
        # 1. Fetch recommendations
        recs = await supabase_client.fetch_all(
            "ai_recommendations",
            filters=[{"op": "eq", "col": "task_id", "val": task_id}]
        )
        if not recs:
            raise ValueError(f"No recommendations found for task {task_id}")

        recs = [r for r in recs if r["id"] in recommendation_ids]
        if not recs:
            raise ValueError("No matching recommendations found for provided IDs")

        # 2. Create deployment plan
        deployment_plan = await self.create_deployment_plan(
            url_id=recs[0]["url_id"],
            recommendation_ids=[r["id"] for r in recs],
            optimization_level=optimization_level,
            task_id=task_id,
            recommendations=[AIRecommendation(**r) for r in recs]
        )

        if not deployment_plan:
            return {"pixel_id": None, "success": False, "error": "Failed to create deployment plan"}

        # 3. Cache & format optimizations
        optimizations = self._format_optimizations([{"ai_recommendations": r} for r in recs])
        cache_key = f"pixel:{recs[0]['url_id']}"
        await RedisCache.cache_set(cache_key, json.dumps(optimizations), ttl=300)

        # Updated: safely pass pixel_id and page_url, with fallback
        pixel_id = recs[0].get("pixel_id") or "<unknown_pixel_id>"
        page_url = recs[0].get("page_url") or "<unknown_page_url>"

        success = await self._deploy_via_pixel(pixel_id, page_url)

        # 5. Return unified result
        return {
            "pixel_id": recs[0]["pixel_id"],
            "success": success
        }


    def _filter_by_optimization_level(self, recs: List[Dict[str, Any]], level: str) -> List[Dict[str, Any]]:
        """
        Filter recommendations based on optimization level.
        Example levels: 'critical', 'high', 'medium', 'low'.
        """
        if not recs:
            return []

        level_priority = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        threshold = level_priority.get(level, 1)

        return [r for r in recs if level_priority.get(r.get("priority", "low"), 1) >= threshold]

    def _create_rollback_strategy(self, recs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create rollback strategy by capturing inverse changes for each recommendation.
        Example: if a meta title was updated, rollback will store the old value.
        """
        strategy = []
        for r in recs:
            if "before" in r and "after" in r:
                strategy.append({
                    "element": r.get("element"),
                    "rollback_to": r["before"],
                    "applied_change": r["after"]
                })
        return {"steps": strategy, "count": len(strategy)}

    def _calculate_risk_level(self, recs: List[Dict[str, Any]]) -> str:
        """
        Calculate risk level based on scope of optimizations.
        High number of structural changes = higher risk.
        """
        if not recs:
            return "low"

        structural_elements = {"schema", "canonical", "robots", "script"}
        structural_changes = sum(1 for r in recs if r.get("element") in structural_elements)

        if structural_changes > 5:
            return "high"
        elif structural_changes > 2:
            return "medium"
        return "low"

    def _identify_dependencies(self, recs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify dependencies between recommendations.
        Example: schema depends on meta updates, canonical depends on URL structure.
        """
        deps = []
        for r in recs:
            if r.get("element") == "canonical":
                deps.append({"id": r.get("id"), "depends_on": "url_structure"})
            if r.get("element") == "schema":
                deps.append({"id": r.get("id"), "depends_on": "meta"})
        return deps

    def _determine_deployment_order(self, recs: List[Dict[str, Any]]) -> List[str]:
        """
        Determine order of deployment: meta → content → schema → scripts.
        """
        priority_order = {"meta": 1, "content": 2, "schema": 3, "script": 4}
        sorted_recs = sorted(
            recs,
            key=lambda r: priority_order.get(r.get("element"), 99)
        )
        return [r.get("id") for r in sorted_recs if r.get("id")]

    def _create_validation_rules(self, recs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create validation rules to check if optimizations were applied correctly.
        """
        rules = []
        for r in recs:
            if r.get("element") == "meta":
                rules.append({"check": "meta_title_exists", "expected": r.get("after")})
            elif r.get("element") == "canonical":
                rules.append({"check": "canonical_matches", "expected": r.get("after")})
            elif r.get("element") == "schema":
                rules.append({"check": "schema_valid_jsonld", "expected": True})
        return rules
    
    async def _log_deployment_activity(self, pixel_id: str, page_url: str, action: str, details: Optional[Dict[str, Any]] = None):
        """Log pixel activity to the pixel_activity table"""
        try:
           # Updated: enforce non-null pixel_id & page_url
            await supabase_client.insert_into(
                "pixel_activity",
                {
                    "pixel_id": pixel_id,
                    "page_url": page_url,
                    "action": action,
                    "details": details or {},
                    "created_at": datetime.utcnow().isoformat()  # ✅ correct column
                }
            )


        except Exception as e:
            logger.warning(f"Failed to log pixel activity for {pixel_id}: {str(e)}")


pixel_service = PixelService()