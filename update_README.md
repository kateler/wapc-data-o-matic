# update-hosted-feature-service

This Python script turns an MXD into a service definition (SD) file. Your ArcGIS.com account is searched for a matching service. The SD file is uploaded to your ArcGIS.com account, the existing service is overwritten with new content.

##### Note! This script was updated August 29, 2014 - The script no longer deletes and re-creates the feature service. It now will overwrite it in place. This means the original itemID of the feature service is maintained and any webmaps that referenced the feature service will continue to work.

See more information on the [associated ArcGIS Blog post](http://blogs.esri.com/esri/arcgis/2014/01/24/updating-your-hosted-feature-service-for-10-2/).
The original blog post for ArcGIS 10.1 can be found [here](http://blogs.esri.com/esri/arcgis/2013/04/23/updating-arcgis-com-hosted-feature-services-with-python/).

## Instructions

1. Download the update.py and settings.ini files. (Hint: Click the `Download ZIP` button on the right)
2. Save these files to your local working directory
3. Download the Python module, `requests`. You can see it on [GitHub here](https://github.com/kennethreitz/requests) or directly download the [zip file here](https://github.com/kennethreitz/requests/archive/master.zip)
4. Open the zip file and save the 'requests' folder to your working directory or deploy to your Python installation
5. Update the settings.ini file to values for your service.
![App](http://blogs.esri.com/esri/arcgis/files/2014/01/fs_ini_props1.jpg)
6. Run the python script

``` 
c:\>c:\Python27\ArcGIS10.2\python.exe c:\myLocalDirectory\update.py
...
Starting Feature Service publish process
found Feature Service : 7ac9e68e9cd341e0a0a217590e4f6265
found Service Definition : bb2261fe2d684e7cb950c6d29372642e
Created D:\myLocalFolder\MyMaps\tempDir\MyMapService.sd
updated SD:   bb2261fe24684e7cb950c6d29372642e
successfully deleted...7ac9e68e9cd34fe0a0f217590e4f6265...
successfully updated...[{u'encodedServiceURL': u'http://services1.arcgis.com/hLJbHVsas2rDIzK0I/arcgis/rest/services/MyMapService/FeatureServer', u'jobId': u'c886b86c-46d4-4be2-95ab-32b284b72dfb', u'serviceurl': u'http://services1.arcgis.com/hLJbHVsas2rDIzK0I/arcgis/rest/services/MyMapService/FeatureServer', u'type': u'Feature Service', u'serviceItemId': u'7df087dfea1b4c7bad2ba372faeefc1c', u'size': 75344}]...
successfully shared...7df087dfea1b4c7bad2ba372faeefc1c...
finished.
```

## Requirements

* ArcGIS 10.2 (or 10.2.1)

## Resources

* [ArcGIS REST API](http://resources.arcgis.com/en/help/arcgis-rest-api/index.html#/The_ArcGIS_REST_API/02r300000054000000/)


## Issues

Find a bug or want to request a new feature?  Please let us know by submitting an issue.

## Contributing

Esri welcomes contributions from anyone and everyone. Please see our [guidelines for contributing](https://github.com/esri/contributing).

## Licensing
Copyright 2013 Esri

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

A copy of the license is available in the repository's [license.txt]( https://github.com/update-hosted-feature-service/master/license.txt) file.

[](Esri Tags: ArcGIS.com Online Update Hosted Feature Services Automate Python Publish)
[](Esri Language: Python)​
