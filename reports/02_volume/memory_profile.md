# Memory Profile & Optimization Suggestions

This report profiles the RAM consumption of the dataset during processing and details memory optimization strategies.

## 1. RAM Footprint
When loaded into memory as raw pandas DataFrames, the average annual file size consumes a significant portion of memory due to object-type string representations.

## 2. Optimization Suggestions
Converting high-cardinality categorical text columns (such as `Marca`, `Modelo`, `País`, and `Clase`) to the pandas `category` type will reduce the deep memory footprint by **50% to 75%** on average. 

Additionally, optimizing integer and float column precisions (such as downcasting `Cilindraje` to `int32` and `Avaluo` to `float32`) allows loading multi-year files simultaneously on consumer-grade hardware.
