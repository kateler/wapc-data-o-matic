## WAPC data-o-matic
 
### Summary:
This script takes a CSV file containing new call records and
cleans, validates, and processes it; appends it to the existing data;
and updates the ArcGIS Online feature service.

### Table of Contents:

1. Introductory settings (setting variables, importing libraries)
1. Import new data table into the geodatabase
  1. Import table
  1. Make sure date field isn't null and try again if so
  1. Make sure date field is in date format
  1. Only keep today's records
1. Clean data
  1. Change county names to title case
  1. Remove non-Washington calls and those from unknown counties
  1. Add spaces to the substance category field for better display
  1. Make sure number fields are the correct field type
1. Geocode the clean data
  1. Geocode with a county-based address locator
  1. Stop and complain if there are unmatched records
1. Add new data to this month's table
1. Delete tables from previous month(s)
1. Create separate feature classes for today's cases and this hour's cases
1. Create feature class for today's choropleth map
  1. Calculate number of cases per county for today
  1. Join today's county totals to the county polygons
1. Delete intermediate tables and feature classes
1. Update the ArcGIS Online feature service (this part taken from [https://github.com/arcpy/update-hosted-feature-service])
