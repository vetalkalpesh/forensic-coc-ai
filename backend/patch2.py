import re, os

d = r'c:\Users\kalpesh\Downloads\forensic\forensic_coc\frontend'

def p(f, onclick_targets):
    pth = os.path.join(d, f)
    with open(pth, 'r', encoding='utf-8') as file: c = file.read()
    for target in onclick_targets:
        # Regex to find button with specific onclick and add req-senior to its class
        pattern = r'(<button[^>]*?class=["\'][^"\']*?)(["\'][^>]*?onclick=["\']' + re.escape(target) + r'["\'])'
        c = re.sub(pattern, r'\1 req-senior\2', c)
    with open(pth, 'w', encoding='utf-8') as file: file.write(c)

p('cases.html', ['openModal(\'addCaseModal\')'])
p('custody.html', ['openModal(\'trModal\')'])
p('forensic.html', ['openModal(\'addExamModal\')', 'openModal(\'reportModal\')'])
p('tamper.html', ['openModal(\'tmModal\')', 'resolve(${t.incident_id})'])
p('storage.html', ['openModal(\'assignModal\')'])

print('Done2')
