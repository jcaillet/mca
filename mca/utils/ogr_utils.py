import shapefile
from shapely.wkt import loads
from shapely.geometry import LineString, Polygon
from osgeo import ogr
from mca.utils.db_utils import getShapelyNodes


def intersectNodes(path, srs, projName, projSRS, isGridProject, gridResolution):
    j = []
    isGridLine = False
    sf = shapefile.Reader(path)
    nodes = list(getShapelyNodes(projName))
    for shape in sf.shapes():
        shType = shape.shapeType
        # http://en.wikipedia.org/wiki/Shapefile#Shapefile_shape_format_.28.shp.29
        if shType == 5: # Polygon
            sh = Polygon(shape.points)
        elif shType == 3: # Line
            if isGridProject:
                sh = LineString(shape.points)
                isGridLine = True
            else:
                pass
        else:
            consoleAppend('Unknown shape type %s. Continue without access' %shType)

        if srs != projSRS:
            sh = shapelyReproject(sh, srs, projSRS)

        if isGridLine:
            sh = sh.buffer(gridResolution)

        for node in nodes:
            if sh.contains(node[1]): # node.geom
                j.append(node[0]) # node.node_id

    return j if j else None


def shapelyReproject(shape, srsF, srsT):
    from_srs = ogr.osr.SpatialReference()
    from_srs.ImportFromEPSG(srsF)
    to_srs = ogr.osr.SpatialReference()
    to_srs.ImportFromEPSG(srsT)

    ogr_geom = ogr.CreateGeometryFromWkb(shape.wkb)
    ogr_geom.AssignSpatialReference(from_srs)
    ogr_geom.TransformTo(to_srs)
    return loads(ogr_geom.ExportToWkt())