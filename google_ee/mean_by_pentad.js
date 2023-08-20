// Import the CSV file as an Earth Engine FeatureCollection
var csvData = ee.FeatureCollection('projects/blsa-366515/assets/pentads')

// Define the list of images and their respective bands
var images = [
  {
    //https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_Landcover_100m_Proba-V-C3_Global
    image: ee.Image("COPERNICUS/Landcover/100m/Proba-V-C3/Global/2019"),
    bands: [
      'grass-coverfraction', 
      'bare-coverfraction', 
      'shrub-coverfraction',
      'tree-coverfraction',
      'water-permanent-coverfraction',
      'water-seasonal-coverfraction'
    ],
    name: 'Landcover'
  },
  {
    //https://developers.google.com/earth-engine/datasets/catalog/NASA_NASADEM_HGT_001
    image: ee.Image('NASA/NASADEM_HGT/001'),
    bands: ['elevation'],
    name: 'NASADEM'
  },
  {
    //https://developers.google.com/earth-engine/datasets/catalog/FAO_WAPOR_2_L1_AETI_D
    image: ee.ImageCollection('FAO/WAPOR/2/L1_AETI_D').first(),
    bands: null,
    name: 'L1_AETI_D'
  },
  {
    //https://developers.google.com/earth-engine/datasets/catalog/FAO_WAPOR_2_L1_NPP_D
    image: ee.ImageCollection('FAO/WAPOR/2/L1_NPP_D').first(),
    bands: null,
    name: 'L1_NPP_D'
  },
  {
    //https://developers.google.com/earth-engine/datasets/catalog/CSP_ERGo_1_0_Global_ALOS_CHILI
    image: ee.Image('CSP/ERGo/1_0/Global/ALOS_CHILI'),
    bands: ['constant'],
    name: 'ALOS_CHILI'
  },
  {
    //https://developers.google.com/earth-engine/datasets/catalog/CSP_ERGo_1_0_Global_ALOS_mTPI
    image: ee.Image('CSP/ERGo/1_0/Global/ALOS_mTPI'),
    bands: ['AVE'],
    name: 'ALOS_mTPI'
  },
  {
    //https://developers.google.com/earth-engine/datasets/catalog/CSP_ERGo_1_0_Global_ALOS_topoDiversity
    image: ee.Image('CSP/ERGo/1_0/Global/ALOS_topoDiversity'),
    bands: ['constant'],
    name: 'ALOS_topoDiversity'
  },
  {
    //https://developers.google.com/earth-engine/datasets/catalog/JAXA_GCOM-C_L3_LAND_LAI_V3
    image: ee.ImageCollection("JAXA/GCOM-C/L3/LAND/LAI/V3")
                .filterDate('2021-12-01', '2022-01-01')
                // filter to daytime data only
                .filter(ee.Filter.eq("SATELLITE_DIRECTION", "D"))
                .mean(),
    bands: ['LAI_AVE'],
    name: 'C_L3_LAND_LAI_V3_DEC_21'
  },
  {
    //https://developers.google.com/earth-engine/datasets/catalog/JAXA_GCOM-C_L3_LAND_LAI_V3
    image: ee.ImageCollection("JAXA/GCOM-C/L3/LAND/LAI/V3")
                .filterDate('2021-06-01', '2021-07-01')
                // filter to daytime data only
                .filter(ee.Filter.eq("SATELLITE_DIRECTION", "D"))
                .mean(),
    bands: ['LAI_AVE'],
    name: 'C_L3_LAND_LAI_V3_JUNE_21'
  },
  {
    //https://developers.google.com/earth-engine/datasets/catalog/ISDASOIL_Africa_v1_sand_content
    image: ee.Image('ISDASOIL/Africa/v1/sand_content'),
    bands: ['mean_0_20'],
    name: 'sand_content'
  },
  {
    //https://developers.google.com/earth-engine/datasets/catalog/ISDASOIL_Africa_v1_ph
    image: ee.Image('ISDASOIL/Africa/v1/ph'),
    bands: ['mean_0_20'],
    name: 'ph'
  },
  {
    //https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD13A2
    image: ee.ImageCollection('MODIS/061/MOD13A2')
                  .filter(ee.Filter.date('2018-01-01', '2018-05-01'))
                  .mean(),
    bands: ['NDVI', 'EVI'],
    name: 'MOD13A2'
  },
  {
    //https://developers.google.com/earth-engine/datasets/catalog/NASA_ORNL_biomass_carbon_density_v1
    image: ee.ImageCollection('NASA/ORNL/biomass_carbon_density/v1').mean(),
    bands: ['agb', 'bgb'],
    name: 'biomass_carbon_density'
  },
  {
    //https://developers.google.com/earth-engine/datasets/catalog/NASA_SMAP_SPL3SMP_E_005
    image: ee.ImageCollection('NASA/SMAP/SPL3SMP_E/005')
                  .filter(ee.Filter.date('2022-06-01', '2022-07-01'))
                  .mean(),
    bands: ['soil_moisture_am', 'soil_moisture_pm'],
    name: 'SPL3SMP_E'
  },
  
  // Add more images and bands here if needed
];

// Convert the CSV data into an ee.FeatureCollection of rectangles
var rectangles = csvData.map(function (row) {
  var x_min = ee.Number(row.get('y_min'));
  var y_min = ee.Number(row.get('x_min'));
  var x_max = ee.Number(row.get('y_max'));
  var y_max = ee.Number(row.get('x_max'));
  var pentad = row.get('pentad');
  return ee.Feature(ee.Geometry.Rectangle([x_min, y_min, x_max, y_max]), { 'pentad': pentad });
});
// Updated function to compute mean values for each grid cell and image
function computeMean(grid, imageObj) {
  var propertiesList = [];
  
  grid = grid.map(function (cell) {
    var properties = { 'pentad': cell.get('pentad') };
    
    if (!imageObj.bands) {
      // If there are no explicit bands, just compute the mean value for the image
      var meanValue = imageObj.image.reduceRegion({
        reducer: ee.Reducer.mean(),
        geometry: cell.geometry(),
        scale: 100,
        maxPixels: 1e6,
        bestEffort: true 
      }).values().get(0); // Get the first (and only) value from the dictionary
      
      var bandName = imageObj.name
      properties[bandName] = meanValue;
    } else {
      imageObj.bands.forEach(function (band) {
        var meanValue = imageObj.image.select(band).reduceRegion({
          reducer: ee.Reducer.mean(),
          geometry: cell.geometry(),
          scale: 100,
          maxPixels: 1e6
        }).get(band);
        
        var bandName = imageObj.name + '_' + band
        properties[bandName] = meanValue;
      });
    }
    return cell.set(properties);
  });
  
  return grid;
}

// Compute the mean values and export the CSV for each image
images.forEach(function (imageObj) {
  var meanValues = computeMean(rectangles, imageObj);
  
  var fileName = 'mean_values_' + imageObj.name;
  
  // Export the results as a CSV file
  Export.table.toDrive({
    collection: meanValues,
    description: fileName,
    fileFormat: 'CSV',
    fileNamePrefix: fileName,
    folder: 'export_folder', // Specify your Google Drive folder here
    selectors: ['pentad'].concat(imageObj.bands ? imageObj.bands.map(function (band) { return imageObj.name + '_' + band }) : [imageObj.name])
  });
});

// Map.addLayer(rectangles, {color: 'blue'}, 'Pentad Rectangles');

// Reduce the meanValues feature collection to an image
// var meanImage = meanValues.reduceToImage(['L1_AETI_D'], ee.Reducer.first());

// // Set visualization parameters
// var visParams = {
//   min: 0,
//   max: 100,
//   palette: ['red', 'yellow', 'green']
// };

// // Add the meanImage layer to the map
// Map.addLayer(meanImage, visParams, 'L1_AETI_D');