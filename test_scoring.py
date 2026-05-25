"""Test the rewritten scoring engine with Facebook URLs."""
import httpx
import time
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

API_URL = "http://107.161.168.216:8000/api/analyze"

TEST_URLS = [
    "https://web.facebook.com/share/p/1EfTBoVsrL/",
    "https://web.facebook.com/factbuddy.pg/posts/pfbid02KASxVQonABiQM9MUpe8JxhnSs1mK8PJFd8fXStZK2RBWYhT6DzBTmfYN6RUebWxQl",
]

def test_url(url: str):
    print(f"\n{'='*70}")
    print(f"Testing: {url}")
    print('='*70)
    
    start = time.time()
    try:
        response = httpx.post(
            API_URL,
            json={"content": url},
            timeout=60.0,
        )
        elapsed = time.time() - start
        
        print(f"Status: {response.status_code}")
        print(f"Response time: {elapsed:.1f}s")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Trust Score: {data['trust_score']}/100")
            print(f"Verdict: {data['verdict']}")
            print(f"Verdict (BN): {data['verdict_bn']}")
            print(f"Confidence: {data['confidence']}")
            print(f"Processing time: {data['processing_time_ms']}ms")
            print(f"\nExplanation (EN): {data['explanation_en']}")
            print(f"Explanation (BN): {data['explanation_bn']}")
            print(f"\nPillars:")
            for p in data['pillars']:
                print(f"  {p['name']}: {p['score']}/100 (weight={p['weight']}) - {p['explanation_en'][:80]}")
            
            # Check success criteria
            print(f"\n--- SUCCESS CRITERIA ---")
            print(f"[{'PASS' if elapsed < 15 else 'WARN' if elapsed < 30 else 'FAIL'}] Response time: {elapsed:.1f}s (target: <15s)")
            print(f"[{'PASS' if data['trust_score'] < 30 or data['trust_score'] > 70 else 'WARN'}] Score differentiation: {data['trust_score']} (not stuck in 40-60)")
            print(f"[{'PASS' if data['confidence'] > 0.5 else 'WARN'}] Confidence: {data['confidence']}")
        else:
            print(f"Error: {response.text[:500]}")
            
    except Exception as e:
        elapsed = time.time() - start
        print(f"FAILED after {elapsed:.1f}s: {e}")

if __name__ == "__main__":
    for url in TEST_URLS:
        test_url(url)
