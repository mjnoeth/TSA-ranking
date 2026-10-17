# Engine vs. committee: ranking accuracy by season

Each row compares the engine's proposed ranks for season N+1 (computed from season N
results) with the ranks the L&S committee actually approved. Weights were tuned on
2026 only; earlier seasons are out-of-sample.

| Season | League | Teams | Exact | Within 1 | Within 2 | Mean abs error | Worst miss | Spearman ρ |
|---|---|---|---|---|---|---|---|---|
| 2023→2024 | North | 38 | 13 (34%) | 26 (68%) | 35 (92%) | 1.11 | 5 | 0.990 |
| 2023→2024 | South | 50 | 17 (34%) | 41 (82%) | 46 (92%) | 0.92 | 3 | 0.996 |
| 2024→2025 | North | 38 | 21 (55%) | 35 (92%) | 38 (100%) | 0.53 | 2 | 0.997 |
| 2024→2025 | South | 50 | 34 (68%) | 48 (96%) | 50 (100%) | 0.36 | 2 | 0.999 |
| 2025→2026 | North | 37 | 17 (46%) | 35 (95%) | 37 (100%) | 0.59 | 2 | 0.997 |
| 2025→2026 | South | 51 | 27 (53%) | 44 (86%) | 48 (94%) | 0.71 | 4 | 0.997 |
| 2026→2027 | North | 37 | 28 (76%) | 36 (97%) | 37 (100%) | 0.27 | 2 | 0.999 |
| 2026→2027 | South | 51 | 34 (67%) | 45 (88%) | 49 (96%) | 0.51 | 4 | 0.998 |

## Combined (North + South)

| Season | Teams | Exact | Within 1 | Within 2 | Mean abs error | Worst miss |
|---|---|---|---|---|---|---|
| 2023→2024 | 88 | 30 (34%) | 67 (76%) | 81 (92%) | 1.00 | 5 |
| 2024→2025 | 88 | 55 (62%) | 83 (94%) | 88 (100%) | 0.43 | 2 |
| 2025→2026 | 88 | 44 (50%) | 79 (90%) | 85 (97%) | 0.66 | 4 |
| 2026→2027 | 88 | 62 (70%) | 81 (92%) | 86 (98%) | 0.41 | 4 |
| **All** | 352 | 191 (54%) | 310 (88%) | 340 (97%) | 0.62 | 5 |

## Teams the engine placed differently

`committee → engine` rank; positive diff = engine ranked the team lower (bigger number).

### 2023→2024 North — 25 of 38 differ

- Black Horse Run: 25 → 20 (-5)
- Lifetime Raleigh: 26 → 29 (+3)
- Hedingham: 30 → 27 (-3)
- Bedford at Falls River: 8 → 6 (-2)
- Quail Hollow: 11 → 13 (+2)
- Riverwood: 12 → 14 (+2)
- Harrington Grove: 13 → 11 (-2)
- Greenway Club: 14 → 12 (-2)
- Stonebridge: 15 → 17 (+2)
- Summerfield North: 21 → 23 (+2)
- Crabtree: 28 → 26 (-2)
- Coachman's Trail: 31 → 33 (+2)
- Wood Valley: 6 → 7 (+1)
- Granite Falls: 7 → 8 (+1)
- Hasentree: 16 → 15 (-1)
- Lake Park: 17 → 16 (-1)
- Springdale: 18 → 19 (+1)
- Manchester: 19 → 18 (-1)
- Heritage of Wake Forest: 20 → 21 (+1)
- Durant Trails: 23 → 24 (+1)
- Oak Park: 24 → 25 (+1)
- Lakemont: 27 → 28 (+1)
- Jewish Community Center: 29 → 30 (+1)
- Wendell: 32 → 31 (-1)
- Banbury Woods & Hunters Landing: 33 → 32 (-1)

### 2023→2024 South — 33 of 50 differ

- Olive Chapel: 8 → 11 (+3)
- WoodCreek: 15 → 18 (+3)
- Weatherstone: 17 → 14 (-3)
- Glenridge: 40 → 43 (+3)
- Scottish Hills: 3 → 1 (-2)
- Medfield: 9 → 7 (-2)
- Twelve Oaks: 20 → 22 (+2)
- Scotts Mill: 23 → 21 (-2)
- Wellsley: 26 → 24 (-2)
- Prestonwood: 1 → 2 (+1)
- Cary Park: 2 → 3 (+1)
- Abbington: 5 → 6 (+1)
- Apex: 6 → 5 (-1)
- Sunset Ridge: 7 → 8 (+1)
- Shepherds Vineyard: 10 → 9 (-1)
- Walden Creek: 11 → 10 (-1)
- Dutchman Downs: 12 → 13 (+1)
- Lochmere: 13 → 12 (-1)
- Brookstone: 14 → 15 (+1)
- Preston Village: 18 → 17 (-1)
- Clubworx: 21 → 20 (-1)
- Highcroft: 22 → 23 (+1)
- Amberly: 24 → 25 (+1)
- Haddon Hall: 25 → 26 (+1)
- Weldon Ridge: 29 → 30 (+1)
- The Reserve: 30 → 29 (-1)
- Charleston Village: 41 → 40 (-1)
- Bentwinds: 42 → 41 (-1)
- Park Village: 43 → 42 (-1)
- Eagle Ridge: 44 → 45 (+1)
- Devereaux: 45 → 44 (-1)
- Wellington Park: 46 → 47 (+1)
- Garner: 47 → 46 (-1)

### 2024→2025 North — 17 of 38 differ

- Riverwood: 14 → 12 (-2)
- Hasentree: 19 → 21 (+2)
- Hawthorne: 33 → 35 (+2)
- North Hills: 7 → 8 (+1)
- North Raleigh: 8 → 7 (-1)
- Bedford at Falls River: 9 → 10 (+1)
- Greenway Club: 10 → 9 (-1)
- Harrington Grove: 12 → 13 (+1)
- Lake Park: 13 → 14 (+1)
- Summerfield North: 20 → 19 (-1)
- Durant Trails: 21 → 20 (-1)
- Jewish Community Center: 26 → 27 (+1)
- Meredith Townes: 27 → 26 (-1)
- Crabtree: 29 → 30 (+1)
- Southall: 30 → 29 (-1)
- Wendell: 34 → 33 (-1)
- Coachman's Trail: 35 → 34 (-1)

### 2024→2025 South — 16 of 50 differ

- Prestonwood: 8 → 6 (-2)
- Eagle Ridge: 41 → 43 (+2)
- Sunset Ridge: 6 → 7 (+1)
- Abbington: 7 → 8 (+1)
- Walden Creek: 14 → 15 (+1)
- WoodCreek: 15 → 14 (-1)
- Highcroft: 23 → 24 (+1)
- Weatherstone: 24 → 23 (-1)
- Holly Glen: 31 → 32 (+1)
- Bella Casa: 32 → 31 (-1)
- Kildaire Farms: 35 → 36 (+1)
- Carpenter Village: 36 → 35 (-1)
- Glenridge: 42 → 41 (-1)
- Harmony: 43 → 42 (-1)
- Crooked Creek: 45 → 46 (+1)
- Charleston Village: 46 → 45 (-1)

### 2025→2026 North — 20 of 37 differ (in committee list only: Jewish Community Center)

- Springdale: 15 → 13 (-2)
- Lifetime Raleigh: 27 → 29 (+2)
- North Hills: 3 → 4 (+1)
- Greystone: 4 → 3 (-1)
- North Raleigh: 6 → 7 (+1)
- Granite Falls: 7 → 6 (-1)
- Wood Valley: 9 → 10 (+1)
- Northbrook: 10 → 9 (-1)
- Harrington Grove: 13 → 14 (+1)
- Bedford at Falls River: 14 → 15 (+1)
- Durant Trails: 19 → 20 (+1)
- Summerfield North: 20 → 19 (-1)
- Hasentree: 22 → 23 (+1)
- Oak Park: 23 → 22 (-1)
- Crabtree: 28 → 27 (-1)
- Wendell: 29 → 28 (-1)
- Coachman's Trail: 31 → 32 (+1)
- Meredith Townes: 32 → 31 (-1)
- Raleigh Racquet: 34 → 35 (+1)
- Hawthorne: 35 → 34 (-1)

### 2025→2026 South — 24 of 51 differ

- Apex: 5 → 9 (+4)
- Weldon Ridge: 25 → 29 (+4)
- Abbington: 9 → 6 (-3)
- Medfield: 7 → 5 (-2)
- Wellsley: 16 → 18 (+2)
- Scotts Mill: 30 → 28 (-2)
- Charleston Village: 43 → 41 (-2)
- Shepherds Vineyard: 6 → 7 (+1)
- Prestonwood: 13 → 14 (+1)
- Clubworx: 14 → 13 (-1)
- Amberly: 17 → 16 (-1)
- Silverton: 18 → 17 (-1)
- Regency: 21 → 22 (+1)
- Oxxford Hunt: 22 → 21 (-1)
- Haddon Hall: 26 → 25 (-1)
- Weatherstone: 27 → 26 (-1)
- Holly Glen: 28 → 27 (-1)
- Bella Casa: 29 → 30 (+1)
- TCC: 33 → 34 (+1)
- Park at West Lake: 34 → 33 (-1)
- Arbor Creek: 41 → 42 (+1)
- Brighton Forest: 42 → 43 (+1)
- Wellington Park: 47 → 48 (+1)
- Harmony: 48 → 47 (-1)

### 2026→2027 North — 9 of 37 differ

- Lake Park: 8 → 6 (-2)
- North Hills: 6 → 7 (+1)
- North Raleigh: 7 → 8 (+1)
- Hedingham: 19 → 20 (+1)
- Quail Hollow: 20 → 19 (-1)
- Coachman's Trail: 28 → 29 (+1)
- Crabtree: 29 → 28 (-1)
- Manchester: 30 → 31 (+1)
- Banbury Woods & Hunters Landing: 31 → 30 (-1)

### 2026→2027 South — 17 of 51 differ

- Scotts Mill: 27 → 31 (+4)
- Garner: 44 → 41 (-3)
- Sunset Ridge: 6 → 8 (+2)
- Lochmere: 11 → 9 (-2)
- Holly Glen: 30 → 28 (-2)
- Haddon Hall: 31 → 29 (-2)
- Shepherds Vineyard: 7 → 6 (-1)
- Abbington: 8 → 7 (-1)
- Medfield: 9 → 10 (+1)
- WoodCreek: 10 → 11 (+1)
- Preston Village: 16 → 17 (+1)
- Olive Chapel: 17 → 16 (-1)
- Bella Casa: 28 → 27 (-1)
- TCC: 29 → 30 (+1)
- The Reserve: 41 → 42 (+1)
- Charleston Village: 42 → 43 (+1)
- Wellington Park: 43 → 44 (+1)
