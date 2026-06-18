#!/usr/bin/env python3
"""Middle-Liddell-Import: Beta-Code→Unicode + Parser → klassische Kandidaten.

Quelle: blinskey/middle-liddell (Perseus TEI, Perseus_text_1999.04.0058.xml),
abgelegt unter data_src/middle_liddell.xml (nicht im Repo, 23 MB).

Erzeugt data_src/ml_candidates.tsv: „Lemma<TAB>englische Glosse", Eigennamen &
Querverweise gefiltert, gegen vorhandene app/data-Lemmata entdoppelt.
Deutsche Übersetzung + Audio passieren in nachgelagerten Batches.
"""
import re, unicodedata, json, glob, os

BETA = {'a':'α','b':'β','g':'γ','d':'δ','e':'ε','z':'ζ','h':'η','q':'θ','i':'ι','k':'κ',
        'l':'λ','m':'μ','n':'ν','c':'ξ','o':'ο','p':'π','r':'ρ','s':'σ','t':'τ','u':'υ',
        'f':'φ','x':'χ','y':'ψ','w':'ω'}
DIA = {')':'̓','(':'̔','/':'́','\\':'̀','=':'͂','|':'ͅ','+':'̈'}

def beta2uni(s):
    out=[]; i=0; n=len(s); up=False; pre=''
    while i<n:
        c=s[i]
        if c=='*': up=True; i+=1
        elif c in DIA: pre+=DIA[c]; i+=1
        elif c.lower() in BETA:
            base=BETA[c.lower()]
            if c.lower()=='s':
                nxt=s[i+1] if i+1<n else ''
                if nxt=='' or (nxt.lower() not in BETA and nxt not in DIA and nxt!='*'): base='ς'
            ch=base.upper() if up else base; up=False; i+=1
            marks=pre; pre=''
            while i<n and s[i] in DIA: marks+=DIA[s[i]]; i+=1
            out.append(unicodedata.normalize('NFC', ch+marks))
        else: out.append(c); i+=1; up=False; pre=''
    return ''.join(out)

def vorhandene_lemmata():
    s=set()
    for f in glob.glob('app/data/*.json'):
        if f.endswith('index.json'): continue
        d=json.load(open(f, encoding='utf-8'))
        for lek in d.get('lektionen',[d]):
            for v in lek.get('vokabeln',[]):
                s.add(v.get('griechisch','').split(',')[0].strip().lstrip('ὁἡτό ').strip())
    return s

def kandidaten():
    x=open('data_src/middle_liddell.xml', encoding='utf-8').read()
    vorh=vorhandene_lemmata()
    out=[]; seen=set()
    for e in re.findall(r'<entry\b[^>]*>(.*?)</entry>', x, re.S):
        mo=re.search(r'<orth[^>]*>([^<]+)</orth>', e)
        mt=re.search(r'<tr[^>]*>([^<]+)</tr>', e)
        if not mo or not mt: continue
        lemma=beta2uni(mo.group(1).strip())
        gloss=re.sub(r'\s+',' ',mt.group(1)).strip(' ,;:')
        if not lemma or not gloss or lemma[0].isupper(): continue   # Eigennamen raus
        if lemma.split(',')[0] in vorh or lemma in seen: continue
        seen.add(lemma); out.append((lemma,gloss))
    return out

if __name__ == '__main__':
    k=kandidaten()
    os.makedirs('data_src', exist_ok=True)
    open('data_src/ml_candidates.tsv','w',encoding='utf-8').write('\n'.join(f'{l}\t{g}' for l,g in k))
    print(f'{len(k)} klassische Kandidaten → data_src/ml_candidates.tsv')
