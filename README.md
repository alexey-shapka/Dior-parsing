Description

1) Get all categories from 3 groups (women, men, kids) because gifts contains the same products.
2) Get all product links from these categories.
3) Find 2 scripts with data (DataLayer, window.initialState) and extract the data, because site gets empty fields if extract from divs.
   - If data is empty, find another script which contains c_myLadyDiorApp.push.
   - Else check variants of product, and if variants exist - get data from window.initialState, else - get data from DataLayer.
   - Some products have the same color and size fields.
