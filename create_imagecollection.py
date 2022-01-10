import ee

def initiate_imagecollection(aoi, startDate : str = '2017-01-01', endDate: str = '2018-01-01', orbit : str = 'ASCENDING'):
    """Function to Initiate Image Collection From Given Parameters
    args:
        aoi (ee.Object): Area of Interest As ee Object (Point, Polygon, Geometry)
        startDate (str) : Starting Date
        endDate (str) : Ending Date
        orbit (str): Obrital Pass Of Either ASCENDING Or DESCENDING

    returns:

    """
    geometry = aoi.geometry()
    geometry_threshold = geometry.area().subtract(1000)

    raw_data = (
    ee.ImageCollection('COPERNICUS/S1_GRD')
    .filterBounds(geometry).map(lambda image: image.clip(geometry))
    .filterDate(startDate, endDate)
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
    .filter(ee.Filter.eq('instrumentMode', 'IW'))
    .filter(ee.Filter.eq('platform_number', 'A'))
    .filter(ee.Filter.eq('orbitProperties_pass',orbit))
    )


    datelist = ee.List(raw_data.aggregate_array('system:time_start')).distinct().sort()
    datelist = datelist.map( lambda d: ee.Date(d).format('YYYY-MM-dd'))
    datelist = datelist.distinct().sort()

    def mosaic_function(d): # Helper Function
        date = ee.Date(d)
        mosaic_group = raw_data.filterDate(date,date.advance(1,'day')).map(lambda image:image.set('Geometry_Area', image.geometry().area()))
        date_time = mosaic_group.aggregate_array('system:time_start').get(0)
        geometry_area = mosaic_group.aggregate_array('Geometry_Area').reduce(ee.Reducer.sum())
        mosaic_img = mosaic_group.mosaic()
        return mosaic_img.set('system:time_start', date_time).set('Geometry_Area', geometry_area)

    data = (
        ee.ImageCollection(datelist.map(mosaic_function))
        .map(lambda image: image.set('Geometry_Check', ee.Number(image.get('Geometry_Area')).lt(geometry_threshold)))
        .filterMetadata('Geometry_Area', 'not_less_than', geometry_threshold)
    )

    return data
