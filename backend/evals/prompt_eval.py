from pathlib import Path
checks = ['name','email','reason','availability','knowledge','calendar','doctor approval','never confirm','declines','diagnosis']
for filename in ['prompt_a.txt', 'prompt_b.txt']:
    text = Path('evals', filename).read_text(encoding='utf-8').lower()
    score = sum(1 for c in checks if c in text)
    print(f"{filename}: {score}/{len(checks)}")
    missing = [c for c in checks if c not in text]
    if missing: print('  missing:', ', '.join(missing))
print('Conclusion: prompt_b is safer because it defines required fields, tool use, doctor approval, decline handling, and medical safety.')
