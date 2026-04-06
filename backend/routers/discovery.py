"""
Discovery router - Lead discovery and search endpoints.
"""

from fastapi import APIRouter

from backend.config import logger

router = APIRouter(tags=["Discovery"])


from fastapi import WebSocket, WebSocketDisconnect, Query  # noqa: E402
import asyncio  # noqa: E402

from backend.services.crawler import Crawler  # noqa: E402


def _build_rich_offer_context(role: str) -> str:
    """
    Build a rich offer context string for resonance scoring.
    Combines the search role with the user's Brain Context (skills, portfolio)
    so that resonance scores are personalized, not just keyword matches.
    """
    from backend.config import get_supabase

    # Start with the search role
    context_parts = [f"Looking for {role} opportunities and connections."]

    try:
        sb = get_supabase()
        if sb:
            brain_data = (
                sb.table("brain_context").select("*").eq("id", 1).execute().data
            )
            if brain_data:
                brain = brain_data[0]
                skills = brain.get("extracted_skills") or []
                if skills:
                    context_parts.append(
                        f"My skills: {', '.join(skills[:15])}."
                    )
                portfolio = brain.get("portfolio_summary") or ""
                if portfolio:
                    context_parts.append(portfolio[:300])
                tone = brain.get("preferred_tone") or ""
                if tone:
                    context_parts.append(f"Communication style: {tone}.")
    except Exception as e:
        logger.debug(f"Could not fetch brain context for scoring: {e}")

    return " ".join(context_parts)


@router.websocket("/ws/discover")
async def websocket_discover(
    websocket: WebSocket, role: str = Query(...), limit: int = Query(20)
):
    """Stream discovery results directly via WebSocket."""
    await websocket.accept()
    try:
        await websocket.send_json(
            {"status": "running", "message": f"Starting search for {role}..."}
        )

        # Build rich offer context for resonance scoring (P1 Fix #1)
        offer_context = _build_rich_offer_context(role)

        # Track seen person names for deduplication (P1 Fix B)
        seen_persons: set = set()

        crawler = Crawler()

        async def process_and_stream(raw_lead):
            try:
                from backend.services.lead_processor import polish_single_lead
                from backend.services.email_generator import EmailGenerator
                from backend.services.email_verifier import verify_email
                from backend.services.recommendation import recommendation_service
                from backend.services.confidence import ConfidenceScorer

                # A. Polish single lead (ultra fast)
                lead = await polish_single_lead(raw_lead)

                # --- Person-level deduplication (P1 Fix B) ---
                name = lead.get("name", "").strip().lower()
                company = lead.get("company", "").strip().lower()
                person_key = f"{name}|{company}" if name and name != "unknown" else None

                if person_key and person_key in seen_persons:
                    logger.info(f"Duplicate person detected: {name} at {company}. Skipping.")
                    return None
                if person_key:
                    seen_persons.add(person_key)

                # --- Soft filter for non-hiring posts (P0 Fix #3) ---
                # Instead of silently dropping, downgrade resonance and tag
                is_hiring = lead.get("is_hiring_post")
                if is_hiring is False:
                    lead["_unverified_hiring"] = True
                    logger.info(f"AI flagged '{name}' as non-hiring — keeping with penalty.")

                # B. Email prediction & verification (P1 Fix #5: try top 3)
                lead_name = lead.get("name", "Unknown Candidate")
                lead_company = lead.get("company", "Unknown")
                url = lead.get("url", "")

                lead["linkedin_url"] = url
                lead["result_type"] = "person"

                # --- Rich resonance scoring (P1 Fix #1) ---
                raw_score = recommendation_service.calculate_resonance_score(
                    lead, offer_context=offer_context
                )
                resonance = round(float(raw_score) / 100.0, 2)

                # Apply penalty for unverified hiring posts
                if lead.get("_unverified_hiring"):
                    resonance = round(resonance * 0.6, 2)  # 40% penalty

                lead["resonance_score"] = resonance
                lead["email_confidence"] = 0

                # --- Try top 3 email patterns (P1 Fix #5) ---
                best_email = None
                best_confidence = 0

                guesses = EmailGenerator.get_top_guesses(lead_name, lead_company, limit=3)
                for guess in guesses:
                    candidate_email = guess.get("email")
                    if not candidate_email:
                        continue
                    try:
                        verification = await verify_email(candidate_email)
                        status = verification.get("status", "unknown")

                        if status == "valid":
                            # Found a verified email — use it immediately
                            best_email = candidate_email
                            best_confidence = guess.get("confidence", 80)
                            lead["email_verification"] = verification
                            break
                        elif status == "risky" and not best_email:
                            # Keep as fallback
                            best_email = candidate_email
                            best_confidence = guess.get("confidence", 40)
                            lead["email_verification"] = verification
                        # If invalid, try next pattern
                    except Exception:
                        continue

                lead["email"] = best_email
                lead["email_confidence"] = best_confidence

                # --- Integrate ConfidenceScorer (P1 Fix #7) ---
                lead = ConfidenceScorer.score(lead)

                # Clean up internal fields before sending to frontend
                lead.pop("_unverified_hiring", None)
                lead.pop("_data_quality", None)

                # C. STREAM RESULT TO WEBSOCKET IMMEDIATELY
                await websocket.send_json({"status": "lead_discovered", "lead": lead})
                return lead
            except Exception as e:
                logger.error(f"Error in process_and_stream: {e}")
                import traceback

                logger.error(traceback.format_exc())
                return None

        tasks = []

        # Stream results & instantly fire processing tasks (P0 Fix #6: pass limit)
        async for r in crawler.crawl_stream(role, limit=limit):
            if r["type"] == "raw_result":
                task = asyncio.create_task(process_and_stream(r["data"]))
                tasks.append(task)
            elif r["type"] == "status":
                await websocket.send_json({"status": "running", "message": r["data"]})

        if not tasks:
            await websocket.send_json({"status": "completed", "results": []})
            return

        await websocket.send_json(
            {
                "status": "running",
                "message": f"Found {len(tasks)} leads. Finalizing AI polishing and email verification...",
            }
        )

        # Wait for all background tasks to finish processing before closing
        results = await asyncio.gather(*tasks)

        # Filter out dropped (None) results
        valid_results = [r for r in results if r is not None]

        await websocket.send_json({"status": "completed", "results": valid_results})

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"status": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
