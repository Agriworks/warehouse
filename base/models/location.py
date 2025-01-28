from mongoengine import EmbeddedDocument, StringField, FloatField, ListField, EmbeddedDocumentField, DictField

class GeoPoint(EmbeddedDocument):
    """
    Represents a geographic point with latitude and longitude
    """

    latitude = FloatField(required=True, min_value=-90, max_value=90)
    longitude = FloatField(required=True, min_value=-180, max_value=180)

    def to_dict(self) -> dict:
        return {
            'latitude': self.latitude,
            'longitude': self.longitude
        }


class LocationUnit(EmbeddedDocument):
    """
    Represents a single location unit at any level
    """

    name = StringField(required=True)
    level = StringField(
        required=True, 
        choices=['country', 'state', 'district', 'administrative_division', 'city', 'village'],
    )
    

class LocationHierarchy(EmbeddedDocument):
    """
    Represents the full hierarchical structure of a location
    """

    country = StringField(required=True)
    state = StringField()
    district = StringField()
    administrative_division = StringField()
    village = StringField()
    geo_point = EmbeddedDocumentField(GeoPoint)
    

class LocationSpan(EmbeddedDocument):
    """
    Defines the spatial coverage of a dataset across multiple locations
    """

    # List of all unique administrative units in the dataset
    units = ListField(EmbeddedDocumentField(LocationUnit))
    
    # Hierarchical coverage - lists of unique values at each level
    countries = ListField(StringField())
    states = ListField(StringField())
    districts = ListField(StringField())
    administrative_divisions = ListField(StringField())
    cities_villages = ListField(StringField())
    
    # Geographic bounds
    min_lat, max_lat, min_long, max_long = FloatField()
    
    ## TODO: For complex geographic relationships - under construction
    # geojson = DictField()
    
    # def add_location(self, location: LocationHierarchy):
    #     """
    #     Updates span information based on a new location
    #     """
    #     if location.country and location.country not in self.countries:
    #         self.countries.append(location.country)
    #     if location.state and location.state not in self.states:
    #         self.states.append(location.state)
    #     if location.district and location.district not in self.districts:
    #         self.districts.append(location.district)
    #     if location.administrative_division and location.administrative_division not in self.administrative_divisions:
    #         self.administrative_divisions.append(location.administrative_division)
    #     if location.city_village and location.city_village not in self.cities_villages:
    #         self.cities_villages.append(location.city_village)
            
    #     # Update geographic bounds if geo_point exists
    #     if location.geo_point:
    #         if self.min_lat is None or location.geo_point.latitude < self.min_lat:
    #             self.min_lat = location.geo_point.latitude
    #         if self.max_lat is None or location.geo_point.latitude > self.max_lat:
    #             self.max_lat = location.geo_point.latitude
    #         if self.min_long is None or location.geo_point.longitude < self.min_long:
    #             self.min_long = location.geo_point.longitude
    #         if self.max_long is None or location.geo_point.longitude > self.max_long:
    #             self.max_long = location.geo_point.longitude
