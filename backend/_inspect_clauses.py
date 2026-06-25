from core.models import Clause, Contract

contracts = list(Contract.objects.all()[:2])
for c in contracts:
    print(f'=== {c.filename} ===')
    clauses = list(Clause.objects.filter(contract=c))
    for cl in clauses:
        txt = cl.extracted_text or ''
        preview = repr(txt[:80])
        print(f'  {cl.clause_name}: {len(txt)} chars | confidence={cl.confidence} | text_preview={preview}')
    print()
