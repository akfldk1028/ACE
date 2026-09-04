#!/usr/bin/env python
import sys, json, os

path = r'D:/Data/25_ACE/ARR/backend/tmp_mass_check/_massv2/inputs/gen-agent04.json'
d = json.load(open(path, encoding='utf-8'))
schemes = d['schemes']
print(f'Before: {len(schemes)}', file=sys.stderr)

new_sentences = [
  {
    'name': 'low_hall_lodge_with_roof',
    'primary_language': 'solid_body',
    'secondary_language': 'a wide three-storey hall body with a slender bar lodged over its open-face edge, the whole body under a warped plate with one corner raised - a hall and its bridge as a directed flying-eave pair',
    'formal_principle': 'The hall needs a servant bar of offices above it at the street face; lodging the bar over the hall edge so it projects both ways gives the hall its bridge, and raising one corner of the roof toward the open face makes both a directional pair rather than a stack.',
    'dominant_gesture': 'a hall-and-lodge pair under a directed flying eave',
    'reference_basis': 'authored new work',
    'floor_height_m': 3.4,
    'ops': [
      {
        'op': 'extrude',
        'profile': 'square',
        'height': 0.45,
        'storeys': 3,
        'why': 'Input: a wide three-storey hall as the civic base; the body is the host for the lodged bar. Limit: height 0.45 declares mid-low.'
      },
      {
        'op': 'lodge',
        'size': 0.22,
        'over': 0.32,
        'height': 0.55,
        'at': 0.18,
        'why': 'Input: the office bar lodges over the hall edge and projects toward the open face; at 0.18 pushes the lodge toward the street. Limit: size 0.22 keeps the bar slender; over 0.32 spans a third of the hall depth; height 0.55 makes the lodged bar taller than the hall.'
      },
      {
        'op': 'roof',
        'rise': 0.75,
        'eave': 0.32,
        'corners': 'one',
        'sag': 0.1,
        'thin': 0.10,
        'why': 'Input: one corner of the combined body roof plate is raised toward the open face, threading the hall-and-lodge pair with a single directional gesture. Limit: rise 0.75 inside cap; eave 0.32; thin 0.10 is a plate.'
      }
    ]
  },
  {
    'name': 'nest_tower_with_tent_base_roof',
    'primary_language': 'solid_body',
    'secondary_language': 'a two-storey chamfered host body with a narrower tower nested inside and turned 30 degrees, the host wearing a warped plate with all four corners raised - a tower rising from a tensile-tent base',
    'formal_principle': 'The nested tower declares its rotation by rising proud above its host; raising all four corners of the host roof plate turns the base into a tent whose eaves reach outward while the tower rises from its centre - the base and tower are in formal opposition.',
    'dominant_gesture': 'a rotated tower rising from a four-corner tent base',
    'reference_basis': 'authored new work',
    'floor_height_m': 3.4,
    'ops': [
      {
        'op': 'extrude',
        'profile': 'chamfered',
        'height': 0.35,
        'storeys': 2,
        'why': 'Input: a low chamfered host body that reads as a base; two storeys declares the datum. Limit: height 0.35 declares low.'
      },
      {
        'op': 'nest',
        'size': 0.38,
        'proud': 0.85,
        'turn': 30,
        'why': 'Input: a tower is nested inside the host and turned 30 degrees to face the open face; proud 0.85 means the tower rises well above the host. Limit: size 0.38 gives the tower a real floor plate; turn 30 reads clearly in silhouette.'
      },
      {
        'op': 'roof',
        'rise': 0.6,
        'eave': 0.42,
        'corners': 'all',
        'sag': 0.38,
        'thin': 0.09,
        'why': 'Input: all four corners of the host base roof plate are raised to form a tent whose eaves reach beyond the chamfered footprint; the deeply-sagging centre makes the tent read as a catenary surface. Limit: rise 0.6 inside cap; eave 0.42; sag 0.38; thin 0.09.'
      }
    ]
  },
  {
    'name': 'aggregate_three_oval_vault_civic_base',
    'primary_language': 'solid_body',
    'secondary_language': 'three tall oval stems merged at their base, the merged ground body under a barrel vault - three towers emerging from a vaulted hall',
    'formal_principle': 'Three programme towers share a civic hall at grade; merging their bases into one continuous ground body and vaulting its roof declares the hall as the building public room - the vault is the signal of the hall, the three oval stems above are the building identity in the sky.',
    'dominant_gesture': 'three oval towers emerging from a vaulted civic base',
    'reference_basis': 'authored new work',
    'floor_height_m': 3.4,
    'ops': [
      {
        'op': 'aggregate',
        'n': 3,
        'spread': 1.2,
        'height': 0.82,
        'tie': 0.20,
        'profile': 'oval',
        'storeys': 5,
        'why': 'Input: three tall oval stems; spread 1.2 keeps them close enough for a merged base. Limit: height 0.82 declares tall; tie 0.20 binds the lower fifth of each stem.'
      },
      {
        'op': 'merge',
        'height': 0.20,
        'why': 'Input: the base 20 percent of the three stems is merged into one civic hall body. Limit: merge height 0.20 stops the union before the stems individual identities.'
      },
      {
        'op': 'vault',
        'rise': 0.65,
        'bays': 1,
        'along': 'long',
        'why': 'Input: the merged hall base gets a barrel vault so the public room ceiling is a curve, distinguishing it from the flat-plate floors in the oval stems above. Limit: rise 0.65 inside the 1.5-storey cap; one bay keeps the silhouette clear.'
      }
    ]
  }
]

schemes_new = schemes + new_sentences
with open(path, 'w', encoding='utf-8') as f:
    json.dump({'schemes': schemes_new}, f, ensure_ascii=False, indent=2)

rc = sum(1 for x in schemes_new if any(o.get('op')=='roof' for o in x['ops']))
print(f'After: {len(schemes_new)}, roof: {rc}', file=sys.stderr)
