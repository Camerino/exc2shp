from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django import forms
import xlrd, shapefile, os, tempfile, os.path, shutil
from models import Shpfile, Feature, Attribute,AttributeValue
from django.contrib.gis.geos.geometry import GEOSGeometry
from osgeo import ogr
import utils

CHARACTER_ENCODINGS = [("ascii", "ASCII"), ("latin1", "Latin-1"), ("utf8", "UTF-8")]

class ImportExcForm(forms.Form):
    import_exc = forms.FileField(label="Select an Excel file")
    character_encoding = forms.ChoiceField(choices=CHARACTER_ENCODINGS, initial="utf8")

def importexc(request):
    if request.method == "GET":
        form = ImportExcForm()
        return render_to_response("importexc.html",
                                  {'form' : form})
    elif request.method == "POST":

        form = ImportExcForm(request.POST,
                             request.FILES)
        if form.is_valid():
            excfile = request.FILES['import_exc']
            character_encoding = request.POST['character_encoding']
            excel_file = xlrd.open_workbook(file_contents=excfile.read())
            filename=excel_file.sheet_names()
            filename = filename[0]
            dirpath = tempfile.mkdtemp()
            sh = excel_file.sheet_by_index(0)
            w = shapefile.Writer(shapefile.POINT)

            w.field('Station','I')
            w.field('Longitude', 'F')
            w.field('Latitude', 'F')
            w.field('Gravel_pc', 'F')
            w.field('Sand_pc', 'F')
            w.field('Mud_pc', 'F')

            for rownum in range(sh.nrows):
                if rownum == 0:
                    continue
                else:
                    x_coord = sh.cell_value(rowx=rownum, colx=1)
                    y_coord = sh.cell_value(rowx=rownum, colx=2)

                    w.point(x_coord, y_coord)

                    w.record(Station=sh.cell_value(rowx=rownum, colx=0),Latitude=sh.cell_value(rowx=rownum, colx=2),
                             Longitude=sh.cell_value(rowx=rownum, colx=1),Gravel_pc=sh.cell_value(rowx=rownum, colx=3),
                             Sand_pc=sh.cell_value(rowx=rownum, colx=4),Mud_pc=sh.cell_value(rowx=rownum, colx=5))

            w.save(os.path.join(dirpath,filename))

            prj = open("%s.prj" % os.path.join(dirpath,filename), "w")
            epsg = 'GEOGCS["WGS 84",DATUM["WGS_1984",SHEROID["WGS84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]'
            prj.write(epsg)
            prj.close()

            for item in os.listdir(dirpath):
                if item.endswith(".shp"):
                    shapefileName = item
                    datasource = ogr.Open(os.path.join(dirpath, shapefileName))
                    layer = datasource.GetLayer(0)
                    layerDefinition = layer.GetLayerDefn()
                    srcSpatialRef = layer.GetSpatialRef()
                    geometryType = layer.GetLayerDefn().GetGeomType()
                    geometryName = utils.ogrTypeToGeometryName(geometryType)

                    shpfile = Shpfile(
                        filename=shapefileName,
                        srs_wkt=srcSpatialRef.ExportToWkt(),
                        geom_type=geometryName,
                        encoding=character_encoding
                    )

                    shpfile.save()

                    attributes = []
                    layerDef = layer.GetLayerDefn()
                    for i in range(layerDef.GetFieldCount()):
                        fieldDef = layerDef.GetFieldDefn(i)
                        attr = Attribute(
                            shpfile=shpfile,
                            name=fieldDef.GetName(),
                            type=fieldDef.GetType(),
                            width=fieldDef.GetWidth(),
                        )
                        attr.save()
                        attributes.append(attr)

                    for i in range(layer.GetFeatureCount()):
                        srcFeature = layer.GetFeature(i)
                        srcGeometry = srcFeature.GetGeometryRef()
                        geometry = GEOSGeometry(srcGeometry.ExportToWkt())
                        geometry = utils.wrapGEOSGeometry(geometry)
                        geometryField = utils.calcGeometryField(geometryName)
                        args = {}
                        args['shpfile'] = shpfile
                        args[geometryField] = geometry
                        feature = Feature(**args)
                        feature.save()

                    for attr in attributes:
                        success,result = utils.getOGRFeatureAttribute(
                            attr,
                            srcFeature,
                            character_encoding
                        )
                        if not success:
                            shutil.rmtree(dirpath)
                            shpfile.delete()
                            return result

                        attrValue = AttributeValue(
                            feature=feature,
                            attribute=attr,
                            value=result
                        )
                        attrValue.save()



            shutil.rmtree(dirpath)



    return HttpResponse("data imported!!")

        #return render_to_response("importexc.html",
                                  #{'form' : form})


