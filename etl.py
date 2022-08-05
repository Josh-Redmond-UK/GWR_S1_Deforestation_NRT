import utils
import ee
ee.Initiialize()

formaAlerts = ee.Image('WRI/GFW/FORMA/alerts')
ecoRegions = ee.FeatureCollection("projects/data-sunlight-311713/assets/SA_Eco_Regions")

formaAlerts = formaAlerts.clip(ecoRegions)
dynamicWorld = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterDate("2016-01-01", "2017-01-01").mean().unmask()
#Map.addLayer(dynamicWorld.select("trees"), {min:0, max:1, palette:['brown','green']})
# Start at beginning of september 2016 - run until end of april 2019

startDate = ee.Date("2016-09-01")
endDate = ee.Date("2019-05-01")
ascendingCollection = ee.ImageCollection('COPERNICUS/S1_GRD').filter(ee.Filter.eq('orbitProperties_pass', 'ASCENDING')).filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))


descendingCollection = ee.ImageCollection('COPERNICUS/S1_GRD').filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING')).filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))


ascendingAlerts = utils.ShadowDeforestation(ascendingCollection, startDate, endDate)
descendingAlerts = utils.ShadowDeforestation(descendingCollection, startDate, endDate)




s1DeforestationAlert = ee.ImageCollection([ascendingAlerts, descendingAlerts]).qualityMosaic("InverseRCR")
#Map.addLayer(s1DeforestationAlert, {min:1, max:50}, "Radar Alert")

formaDateMask = formaAlerts.select("alert_date").gte(startDate.millis())
#Map.addLayer(formaAlerts.updateMask(formaDateMask).select("alert_delta"), {min:0, max:100, palette:['Blue', 'Green']}, "Forma Alert")

# sampleImage = formaAlerts.updateMask(formaDateMask).select("alert_date").addBands([s1DeforestationAlert]).rename(['FORMA_Alert', 'RADAR_Alert', 'RCR'])

#Map.addLayer(descendingCollection.select("VV").min(), {min:-50, max:1}, "Avg descending backscatter")
#Map.addLayer(sampleImage.unmask())
#print(sampleImage)
testRes = utils.ShadwoGLADTimeseries(16,21)
#print(testRes)
GLADForestChange = ee.Image("UMD/hansen/global_forest_change_2021_v1_9").select("lossyear")
y16Mask = GLADForestChange.eq(16)
#Map.addLayer(GLADForestChange, {min:0, max:21, palette:['yellow', 'red', 'blue']})
reg1 = ecoRegions.filter(ee.Filter.eq("LEVEL3", "20.5.3")).geometry()
#Map.addLayer(reg1, {}, "Testregion")
#Map.addLayer(testRes[16].clip(reg1), {}, "Test Sample Image")
# stratSample = testRes[16].clip(reg1).stratifiedSample({numPoints: 100, classBand: "lossyear", scale:30, tileScale:4})


featureList = ecoRegions.toList(ecoRegions.size())

featureList = ecoRegions.toList(ecoRegions.size())
featColList = ee.List([])
taskList = []
for i in range(featureList.size().getInfo()):
    activeFeat = ee.Feature(featureList.get(i))
    for j in range(16,21):
        activeImg = testRes[j]
        randSample = activeImg.sample(numPixels= 2000, tileScale=4, dropNulls=True, region=activeFeat.geometry(), projection=ee.Image("UMD/hansen/global_forest_change_2021_v1_9").projection())
        #featColList = featColList.add(randSample)
        if len(taskList) >= 998:
          taskList = utils.wait_for_tasks(taskList)
          j -= 1
          continue
        ecoRegionString = activeFeat.get("LEVEL3").getInfo()
        task = ee.batch.Export.table.toDrive(randSample, f"ExportTask{i}-{j}", "GWR_S1_Deforest_NRT\\"+ecoRegionString.replace(".", "\\"), f"{ecoRegionString}-{j}", "csv")
        task.start()


    
    