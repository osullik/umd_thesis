# Graph Benchmarking is H.A.R.D.

## Setup

```
pip install -r requirements.txt
cd gaib
python download_datasets.py
```

GPU runs also need nx-cugraph.

Road network graphs are built with `python md_roads/osmg.py --search_area <name> --area_type STATE|COUNTY|CITY`, then moved from `graphs/` to `gaib/datasets/<name>/`.

## Run

From `gaib/`:

```
python runner.py --hardware <label>
python runner.py --hardware <label> --definitions experiment_definitions/GPU
```

Each run appends a row to `experiment_results/results.csv`.
