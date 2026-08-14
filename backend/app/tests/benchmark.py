import asyncio
import time
from sqlalchemy import text
from app.core.database import SessionLocal

async def run_benchmark():
    async with SessionLocal() as db:
        queries = {
            "GET /grievances (list)": "SELECT * FROM grievances ORDER BY created_at DESC LIMIT 20 OFFSET 0",
            "GET /notifications (list)": "SELECT * FROM notifications ORDER BY created_at DESC LIMIT 20 OFFSET 0",
            "GET /analytics/overview (global metrics)": "SELECT count(id) FROM grievances",
            "GET /supervisor/dossiers (accountability_dossiers)": "SELECT * FROM accountability_dossiers LIMIT 20",
            "GET /grievances/{id}/timeline (events list)": "SELECT * FROM grievance_events ORDER BY created_at ASC"
        }
        
        print("\nSARA SQL QUERY BENCHMARK & INDEX VERIFICATION")
        print("=" * 60)
        
        for name, sql in queries.items():
            start = time.time()
            res = await db.execute(text(sql))
            rows = res.all()
            duration_ms = (time.time() - start) * 1000
            
            print(f"{name}: {len(rows)} rows fetched in {duration_ms:.2f} ms")
            
            explain_res = await db.execute(text(f"EXPLAIN {sql}"))
            explain_rows = explain_res.all()
            print("Query Plan:")
            for row in explain_rows[:3]:
                print(f"  {row[0]}")
            print("-" * 60)

if __name__ == "__main__":
    asyncio.run(run_benchmark())
