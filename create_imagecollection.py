import ee
import restee as ree

def initiate_imagecollection(aoi, startDate : str = '2017-01-01', endDate: str = '2018-01-01', orbit : str = 'ASCENDING'):
    """Function to initiate image collection from given parameters
    args:
        aoi (ee.Object): Area of Interest As ee Object (Point, Polygon, Geometry)
        startDate (str) : Starting Date
        endDate (str) : Ending Date
        orbit (str): Obrital Pass Of Either ASCENDING Or DESCENDING

    returns:
        data (ee.ImageCollection)
    """
    geometry = aoi.geometry()

    # Initiate raw_data image collection
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


    # Mosaic images within one day
    datelist = ee.List(raw_data.aggregate_array('system:time_start')).distinct().sort()
    datelist = datelist.map( lambda d: ee.Date(d).format('YYYY-MM-dd'))
    datelist = datelist.distinct().sort()

    def mosaic_function(d): # Helper Function
        date = ee.Date(d)
        mosaic_group = raw_data.filterDate(date,date.advance(1,'day')).map(lambda image:image.set('Geometry_Area', image.geometry().area()))
        date_time = mosaic_group.aggregate_array('system:time_start').get(0)
        geometry_area = mosaic_group.aggregate_array('Geometry_Area').reduce(ee.Reducer.sum())
        mosaic_img = mosaic_group.mosaic().clip(geometry)
        return mosaic_img.set('system:time_start', date_time).set('Geometry_Area', geometry_area)

    data = (
        ee.ImageCollection(datelist.map(mosaic_function))
    )

    return data


def output_collection(aoi, startDate : str = '2017-01-01', endDate: str = '2018-01-01',):
    """Function to compare collections generate from initiate_imagecollection functions
    and choose collections with more images or bigger maximum geometry area

    args:
        aoi (ee.Object): Area of Interest As ee Object (Point, Polygon, Geometry)
        startDate (str) : Starting Date
        endDate (str) : Ending Date


    returns:

    """
    geometry = aoi.geometry()
    geometry_threshold = geometry.area().subtract(5000)
    # Initiate Image Collections from given parameters
    S1_ImgCol_ASCENDING = initiate_imagecollection(aoi, startDate, endDate, orbit = 'ASCENDING')
    S1_ImgCol_DESCENDING = initiate_imagecollection(aoi, startDate, endDate, orbit = 'DESCENDING')


    # Get maximum geometry area of two image collections
    max_ascending = max(S1_ImgCol_ASCENDING.aggregate_array('Geometry_Area').getInfo())
    max_descending = max(S1_ImgCol_DESCENDING.aggregate_array('Geometry_Area').getInfo())

    if max_ascending < geometry_threshold.getInfo() and max_descending < geometry_threshold.getInfo(): # Both collections don't any image with same geometry as AOI
        # Return collection with bigger maximum geometry area
        if max_ascending >= max_descending:
            min_ascending = min(S1_ImgCol_ASCENDING.aggregate_array('Geometry_Area').getInfo())
            geometry_threshold = (max_ascending - min_ascending)/2
            return (
            S1_ImgCol_ASCENDING
            .map(lambda image: image.set('Geometry_Check', ee.Number(image.get('Geometry_Area')).lt(geometry_threshold)))
            .filterMetadata('Geometry_Area', 'not_less_than', ee.Number(geometry_threshold))
            )
            return S1_ImgCol_ASCENDING
        else:
            min_descending = min(S1_ImgCol_DESCENDING.aggregate_array('Geometry_Area').getInfo())
            geometry_threshold = (max_descending - min_descending)/2
            return (
            S1_ImgCol_DESCENDING
            .map(lambda image: image.set('Geometry_Check', ee.Number(image.get('Geometry_Area')).lt(geometry_threshold)))
            .filterMetadata('Geometry_Area', 'not_less_than', ee.Number(geometry_threshold))
            )
            return S1_ImgCol_DESCENDING
    else: # Choose image collection with more images
        S1_ImgCol_ASCENDING = (
        S1_ImgCol_ASCENDING
        .map(lambda image: image.set('Geometry_Check', ee.Number(image.get('Geometry_Area')).lt(geometry_threshold)))
        .filterMetadata('Geometry_Area', 'not_less_than', geometry_threshold)
        )

        S1_ImgCol_DESCENDING = (
        S1_ImgCol_DESCENDING
        .map(lambda image: image.set('Geometry_Check', ee.Number(image.get('Geometry_Area')).lt(geometry_threshold)))
        .filterMetadata('Geometry_Area', 'not_less_than', geometry_threshold)
        )

        if S1_ImgCol_ASCENDING.size().getInfo() >= S1_ImgCol_DESCENDING.size().getInfo():
            return S1_ImgCol_ASCENDING
        else:
            return S1_ImgCol_DESCENDING
