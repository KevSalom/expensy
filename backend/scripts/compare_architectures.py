import asyncio
import contextlib
import io
import re
import sys
import time
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from supervisor import stream_supervisor_events, stream_single_agent_events


class TimingRedirector:
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout
        self.llm_time = 0.0
        self.airtable_time = 0.0

        # Patterns to parse timing statements
        self.llm_pattern = re.compile(r"\[TIMING\] LLM Call \((.*?)\) took ([\d\.]+)s")
        self.airtable_pattern = re.compile(r"\[TIMING\] Airtable API (\w+) (.*?) took ([\d\.]+)s")

    def write(self, string):
        try:
            self.original_stdout.write(string)
        except UnicodeEncodeError:
            encoding = self.original_stdout.encoding or 'utf-8'
            clean_string = string.encode(encoding, errors='replace').decode(encoding)
            self.original_stdout.write(clean_string)
        self.original_stdout.flush()

        for line in string.splitlines():
            llm_match = self.llm_pattern.search(line)
            if llm_match:
                self.llm_time += float(llm_match.group(2))
            
            airtable_match = self.airtable_pattern.search(line)
            if airtable_match:
                self.airtable_time += float(airtable_match.group(3))

    def flush(self):
        self.original_stdout.flush()


@contextlib.contextmanager
def capture_timings():
    original_stdout = sys.stdout
    redirector = TimingRedirector(original_stdout)
    sys.stdout = redirector
    try:
        yield redirector
    finally:
        sys.stdout = original_stdout


# 2 Read and 2 Write Queries
READ_QUERIES = [
    "Lista los últimos 3 gastos registrados",
    "Busca los gastos del día de hoy"
]

WRITE_QUERIES = [
    "Registra café de 3.5 USD en comida",
    "Gaste 12 USD en taxi hoy"
]


async def run_query(query: str, query_type: str, architecture: str) -> dict:
    start_time = time.time()
    final_response = ""
    
    async def consume_supervisor():
        nonlocal final_response
        async for event in stream_supervisor_events(query, mode="personal"):
            if event["type"] == "final":
                final_response += event["text"]

    async def consume_single():
        nonlocal final_response
        async for event in stream_single_agent_events(query, mode="personal"):
            if event["type"] == "final":
                final_response += event["text"]

    with capture_timings() as redirector:
        try:
            if architecture == "multi_agent":
                await consume_supervisor()
            else:
                await consume_single()
            status = "SUCCESS"
        except Exception as e:
            print(f"\n[ERROR] Query failed: {e}")
            status = f"ERROR: {str(e)[:50]}"

    total_time = time.time() - start_time

    return {
        "query": query,
        "query_type": query_type,
        "status": status,
        "total_time": total_time if status == "SUCCESS" else None,
        "final_response": final_response
    }


async def main():
    print("=" * 80)
    print("Expensy Architecture Comparison Benchmark")
    print("=" * 80)
    print("Comparing Multi-Agent Supervisor vs Single-Agent LCEL Chain")
    print("Model: google/gemini-3.1-flash-lite\n")

    # Force model to Gemini 3.1 Flash Lite
    settings.openai_model = "google/gemini-3.1-flash-lite"

    print("Warming up Multi-Agent Supervisor...")
    try:
        async for _ in stream_supervisor_events("Hola", "personal"): pass
        print("Warmup successful!")
    except Exception as e:
        print(f"Warmup skipped: {e}")

    print("\nWarming up Single-Agent LCEL Chain...")
    try:
        async for _ in stream_single_agent_events("Hola", "personal"): pass
        print("Warmup successful!")
    except Exception as e:
        print(f"Warmup skipped: {e}")

    multi_results = []
    single_results = []

    print("\n--- BENCHMARKING MULTI-AGENT SUPERVISOR ---")
    for q in READ_QUERIES + WRITE_QUERIES:
        q_type = "read" if q in READ_QUERIES else "write"
        print(f"Running '{q}'...")
        res = await run_query(q, q_type, "multi_agent")
        multi_results.append(res)
        await asyncio.sleep(1.5)

    print("\n--- BENCHMARKING SINGLE-AGENT LCEL CHAIN ---")
    for q in READ_QUERIES + WRITE_QUERIES:
        q_type = "read" if q in READ_QUERIES else "write"
        print(f"Running '{q}'...")
        res = await run_query(q, q_type, "single_agent")
        single_results.append(res)
        await asyncio.sleep(1.5)

    # Print Comparative results
    print("\n" + "=" * 100)
    print("ARCHITECTURE COMPARISON SUMMARY")
    print("=" * 100)

    # print statistics
    def calc_averages(results):
        n = len([r for r in results if r["status"] == "SUCCESS"])
        if n == 0:
            return 0.0
        avg_tot = sum(r["total_time"] for r in results if r["status"] == "SUCCESS") / n
        return avg_tot

    m_tot = calc_averages(multi_results)
    s_tot = calc_averages(single_results)

    print(f"\nAverage Latencies (All 4 queries):")
    print(f"{'Metric':<25} | {'Multi-Agent Supervisor':<25} | {'Single-Agent LCEL':<25} | {'Improvement'}")
    print("-" * 90)
    
    improvement_time = m_tot - s_tot
    improvement_pct = (improvement_time / m_tot * 100) if m_tot > 0 else 0.0
    print(f"{'Average Total Latency':<25} | {m_tot:>22.3f}s | {s_tot:>22.3f}s | {improvement_time:>10.3f}s ({improvement_pct:.1f}%)")

    print("\nDetailed Query Comparison Table:")
    print(f"{'Query (first 20)':<20} | {'Type':<5} | {'Multi-Agent Total':<18} | {'Single-Agent Total':<18} | {'Improvement'}")
    print("-" * 80)
    for i, q in enumerate(READ_QUERIES + WRITE_QUERIES):
        q_text = q[:17] + "..." if len(q) > 20 else q
        q_type = "Read" if i < 2 else "Write"
        
        m_res = multi_results[i]
        s_res = single_results[i]
        
        m_time = f"{m_res['total_time']:.3f}s" if m_res["status"] == "SUCCESS" else m_res["status"]
        s_time = f"{s_res['total_time']:.3f}s" if s_res["status"] == "SUCCESS" else s_res["status"]
        
        diff_str = "-"
        if m_res["status"] == "SUCCESS" and s_res["status"] == "SUCCESS":
            diff = m_res["total_time"] - s_res["total_time"]
            diff_str = f"{diff:.3f}s ({(diff/m_res['total_time'])*100:.1f}%)"
            
        print(f"{q_text:<20} | {q_type:<5} | {m_time:>18} | {s_time:>18} | {diff_str}")

if __name__ == "__main__":
    asyncio.run(main())
