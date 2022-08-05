import ee



def ShadowDeforestation(imageCollection, startDate, endDate):
    beforeChangeStart = startDate.advance(-60, "day")

    DEM = ee.Image('CGIAR/SRTM90_V4').select('elevation')
    # To do - change the forest cover mask to update to closest date and use worldcover where available
    forestMask = ee.Image("COPERNICUS/Landcover/100m/Proba-V-C3/Global/2015").select('discrete_classification')
    
    forestMask = forestMask.gte(111).And(forestMask.lte(126))
    
    slope = ee.Terrain.slope(DEM)
    aspect = ee.Terrain.aspect(DEM)
    slopeMask = slope.lte(15)

    s1_GRD_IW = imageCollection.filterDate(beforeChangeStart, endDate).filter(ee.Filter.eq('instrumentMode', 'IW'));
    
    resampled_s1_GRD_IW_VV = s1_GRD_IW.select("VV")
    
    rcrTimeSeries = ee.List([])
    alertTimeSeries = ee.List([])

    windowStart = startDate
    counter = 1
    windowEnd = startDate.advance(36, "day")
    dateRange = ee.DateRange(startDate, endDate)

    # Iterate through the date range and generate before/after image collections using a sliding window
    while (dateRange.contains(windowEnd).getInfo()):
        try:
            before = resampled_s1_GRD_IW_VV.filterDate(windowStart.advance(-36, "day"), windowStart).mean()
            after = resampled_s1_GRD_IW_VV.filterDate(windowStart, windowEnd).mean()
            test_rcr = after.subtract(before)
            avgAngle = imageCollection.filterDate(windowStart.advance(-36, "day"), windowEnd).select("angle").mean()
            windowEnd = windowEnd.advance(24, "day")
            windowStart = windowStart.advance(24, "day")
            # deforestationAlert = test_rcr.lte(-4.5).selfMask()
            # deforestationNeighbours = test_rcr.lte(-3)
            # cumCost = deforestationNeighbours.cumulativeCost(deforestationAlert.updateMask(slopeMask), 2000, false).lt(1)
        #print(ee.Image.constant(ee.Number(startDate.millis())))
            deforestationDate = ee.Image.constant(ee.Number(startDate.millis())).cast({"constant":"float"})#.updateMask(cumCost)#.cast({"constant":"long"})
            rcrLong = test_rcr#.multiply(100).cast({"VV":"long"})
            rcrQualBand = rcrLong.multiply(-1)
            deforestationDate = deforestationDate.addBands([rcrLong, slope, aspect, avgAngle, rcrQualBand]).rename("Date", "RCR", "Slope", "Aspect", "Satellite Angle", "InverseRCR")
            counter +=1
            alertTimeSeries = alertTimeSeries.add(test_rcr)
            rcrTimeSeries = rcrTimeSeries.add(deforestationDate)
        except:
            pass
      
  #print("RCR Collection finished")
    rcrCollectionMin = ee.ImageCollection(rcrTimeSeries).qualityMosaic("InverseRCR").updateMask(forestMask)
  # MMUMask = rcrCollectionMin.gt(0).connectedComponents(ee.Kernel.plus(1), 10).mask()
  #MMUMask = MMUMask.select("labels").and(MMUMask.select("Date"))
    
    return rcrCollectionMin 
    

def ShadwoGLADTimeseries(startYear, endYear):
    GLADForestChange = ee.Image("UMD/hansen/global_forest_change_2021_v1_9").select("lossyear")
    ascendingCollection = ee.ImageCollection('COPERNICUS/S1_GRD').filter(ee.Filter.eq('orbitProperties_pass', 'ASCENDING')).filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))


    descendingCollection = ee.ImageCollection('COPERNICUS/S1_GRD').filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING')).filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
      

    intDateDict = {16:ee.Date("2016-01-01"), 17:ee.Date("2017-01-01"), 18:ee.Date("2018-01-01") , 19:ee.Date("2019-01-01"), 20:ee.Date("2020-01-01") , 21:ee.Date("2021-01-01")}
    resultsDict = {}
    for  i in range(startYear, endYear):
        Y = GLADForestChange.eq(i).unmask()
        startDate = intDateDict[i]
        endDate = intDateDict[i+1].advance(-1, "day")
        ascendingAlert = ShadowDeforestation(ascendingCollection, startDate, endDate)
        descendingAlert = ShadowDeforestation(descendingCollection, startDate, endDate)
        s1DeforestationAlert = ee.ImageCollection([ascendingAlert, descendingAlert]).qualityMosaic("InverseRCR")

        XY = s1DeforestationAlert.addBands(Y)
        resultsDict[i] = XY
      

    return resultsDict

def wait_for_tasks(task_list):
  for t in task_list:
    if t.status()['state']=='COMPLETED':
      task_list.remove(t)
  return task_list
