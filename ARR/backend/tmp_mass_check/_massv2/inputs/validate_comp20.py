import json
path = r'D:\Data\25_ACE\ARR\backend\tmp_mass_check\_massv2\inputs\gen-comp20.json'
d = json.load(open(path, encoding='utf-8'))
schemes = d['schemes']
print('COUNT:', len(schemes))
openers = {'extrude','loop','aggregate','stack'}
errors = []
req = {'name','primary_language','secondary_language','formal_principle','dominant_gesture','reference_basis','floor_height_m','ops'}
for s in schemes:
    n = s['name']
    miss = req - set(s.keys())
    if miss: errors.append(n+' missing '+str(miss))
    ops = s.get('ops',[])
    if not ops: errors.append(n+' no ops'); continue
    if ops[0]['op'] not in openers: errors.append(n+' first='+ops[0]['op']+' not opener')
    for j,op in enumerate(ops):
        v = op['op']
        if 'why' not in op: errors.append(n+'['+str(j)+'] '+v+' no why')
    for j,op in enumerate(ops):
        v = op['op']
        if v=='cantilever':
            r = op.get('reach',0)
            if r>0.40: errors.append(n+' cantilever reach '+str(r)+' > 0.40')
        if v=='lift':
            c = op.get('clearance',0.2)
            if not(0.1<=c<=0.40): errors.append(n+' lift clearance '+str(c)+' OOR')
        if v=='inscribe':
            dep = op.get('depth',0.3)
            if not(0.1<=dep<=0.5): errors.append(n+' inscribe depth '+str(dep)+' OOR')
        if v=='aggregate':
            sp = op.get('spread',1.0)
            tie = op.get('tie',0)
            if sp<1.05 or sp>2.5: errors.append(n+' aggregate spread '+str(sp)+' OOR')
            if tie<0 or tie>0.4: errors.append(n+' aggregate tie '+str(tie)+' OOR')
        if v=='split':
            r = op.get('ratio',0.5)
            c2 = op.get('contrast',1.5)
            g = op.get('gap',0)
            if not(0.3<=r<=0.75): errors.append(n+' split ratio '+str(r)+' OOR')
            if not(1.2<=c2<=3.5): errors.append(n+' split contrast '+str(c2)+' OOR')
            if g>0 and g*0.76<3.9: errors.append(n+' split gap '+str(g)+' real='+str(round(g*0.76,2))+'m < 3.9m')
        if v=='stagger':
            r = op.get('ratio',0.3)
            if not(0.15<=r<=0.95): errors.append(n+' stagger ratio '+str(r)+' OOR')
        if v=='carve':
            sz = op.get('size',0.3)
            if not(0.15<=sz<=0.6): errors.append(n+' carve size '+str(sz)+' OOR')
        if v=='reflect':
            if 'clear' not in op: errors.append(n+' reflect no clear')
            elif not(1.0<=op['clear']<=1.6): errors.append(n+' reflect clear '+str(op['clear'])+' OOR')
        if v=='join':
            lv = op.get('level',0)
            if not(0.0<=lv<=0.6): errors.append(n+' join level '+str(lv)+' OOR')
        if v=='fold':
            ff = op.get('folds',1)
            if ff>3: errors.append(n+' fold folds '+str(ff)+' > 3')
    carves = sum(1 for o in ops if o['op']=='carve')
    if carves == 0: errors.append(n+' ZERO carves')
if errors:
    print('ERRORS:')
    for e in errors: print('  '+e)
else:
    print('VALIDATION PASS - 0 errors')
print('Carves per scheme:')
for s in schemes:
    c = sum(1 for o in s['ops'] if o['op']=='carve')
    print('  '+s['name']+': '+str(c))
print('Openers:')
for s in schemes:
    print('  '+s['name']+': '+s['ops'][0]['op'])
