import re, os

d = r'c:\Users\kalpesh\Downloads\forensic\forensic_coc\frontend'

def p(f, pats):
    pth = os.path.join(d, f)
    with open(pth, 'r', encoding='utf-8') as file: c = file.read()
    for o, n in pats: c = re.sub(o, n, c)
    with open(pth, 'w', encoding='utf-8') as file: file.write(c)

# cases.html
p('cases.html', [
    (r'<div class="form-group"><label class="form-label">Investigating Officer \*</label><select class="form-control" id="officer"></select></div>', ''),
    (r"populateSelect\('officer',o,'officer_id','full_name'\);", ''),
    (r"investigating_officer_id:document\.getElementById\('officer'\).value,", '')
])

# custody.html (trFrom is already removed by the successful part of previous tool)
# Let's fix the remaining parts
p('custody.html', [
    (r"transferred_by:document.getElementById\('trFrom'\).value,", "")
])

# court.html
p('court.html', [
    (r'<div class="form-group"><label class="form-label">Submitted By \*</label><select class="form-control" id="subOfficer"></select></div>', ''),
    (r"populateSelect\('subOfficer',officers,'officer_id','full_name'\);", ''),
    (r"submitted_by:document\.getElementById\('subOfficer'\).value,", "")
])

# forensic.html
p('forensic.html', [
    (r'<div class="form-group"><label class="form-label">Filed By \*</label><select class="form-control" id="rOfficer"></select></div>', ''),
    (r"populateSelect\('rOfficer',officers,'officer_id','full_name'\);", ''),
    (r"filed_by:document\.getElementById\('rOfficer'\).value,", "")
])

# tamper.html
p('tamper.html', [
    (r'<div class="form-group"><label class="form-label">Reported By \*</label><select class="form-control" id="tmOfficer"></select></div>', ''),
    (r"populateSelect\('tmOfficer',officers,'officer_id','full_name'\);", ''),
    (r"reported_by:document\.getElementById\('tmOfficer'\).value,", "")
])

print("Patched all.")
