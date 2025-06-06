from typing import List, Dict, Optional
from models.location import LocationHierarchy, GeoPoint
from models.time import TimePoint
from models.dataset import Dataset
from geopy.distance import geodesic


class DatasetMerger:
    def __init__(self, dataset1: Dataset, dataset2: Dataset):
        self.dataset1 = dataset1
        self.dataset2 = dataset2
        self.spatial_hierarchy = ['country', 'state', 'district', 'administrative_division', 'city_village']

    def is_location_contained(self, loc1: LocationHierarchy, loc2: LocationHierarchy) -> bool:
        """
        Checks if loc2 is contained within loc1's administrative hierarchy
        """

        if loc1.country and loc1.country != loc2.country:
            return False
            
        if loc1.state and loc1.state != loc2.state:
            return False
            
        if loc1.district and loc1.district != loc2.district:
            return False
            
        if loc1.administrative_division and loc1.administrative_division != loc2.administrative_division:
            return False
            
        if loc1.city_village and loc1.city_village != loc2.city_village:
            return False
            
        return True


    def get_location_specificity(self, location: LocationHierarchy) -> int:
        """
        Returns how specific a location is (0 = country only, 4 = village level)
        """

        specificity = 0
        if location.state:
            specificity += 1
        if location.district:
            specificity += 1
        if location.administrative_division:
            specificity += 1
        if location.city_village:
            specificity += 1
        return specificity


    def get_most_specific_location(self, loc1: LocationHierarchy, loc2: LocationHierarchy) -> LocationHierarchy:
        """
        Returns the more specific of two locations
        """

        spec1 = self.get_location_specificity(loc1)
        spec2 = self.get_location_specificity(loc2)
        return loc1 if spec1 >= spec2 else loc2


    def calculate_distance(self, point1: GeoPoint, point2: GeoPoint) -> float:
        """
        Calculates distance between two points in kilometers
        """

        return geodesic(
            (point1.latitude, point1.longitude),
            (point2.latitude, point2.longitude)
        ).kilometers


    def find_nearest_point(self, loc1: LocationHierarchy, loc2: LocationHierarchy, threshold: float = 50.0) -> bool:
        """
        Determines if two locations are within threshold kilometers of each other
        """

        if not (loc1.geo_point and loc2.geo_point):
            return False
            
        distance = self.calculate_distance(loc1.geo_point, loc2.geo_point)
        return distance <= threshold


    def compute_weighted_location(self, loc1: LocationHierarchy, loc2: LocationHierarchy) -> LocationHierarchy:
        """
        Creates a weighted average location based on distance
        """

        if not (loc1.geo_point and loc2.geo_point):
            return loc1

        # Create new location with administrative info from more specific location
        result = self.get_most_specific_location(loc1, loc2)
        
        # Calculate weighted average of coordinates (equal weights)
        weight1 = weight2 = 0.5
        new_lat = (loc1.geo_point.latitude * weight1 + loc2.geo_point.latitude * weight2)
        new_long = (loc1.geo_point.longitude * weight1 + loc2.geo_point.longitude * weight2)
        
        result.geo_point = GeoPoint(latitude=new_lat, longitude=new_long)
        return result


    def do_periods_overlap(self, time1: TimePoint, time2: TimePoint) -> bool:
        """
        Checks if two time periods overlap
        """

        dt1 = time1.to_datetime()
        dt2 = time2.to_datetime()
        
        # Consider granularity
        if not time1.month or not time2.month:
            return time1.year == time2.year
        if not time1.day or not time2.day:
            return time1.year == time2.year and time1.month == time2.month
        return dt1 == dt2


    def is_time_contained(self, time1: TimePoint, time2: TimePoint) -> bool:
        """
        Checks if time2 is contained within time1's period
        """

        if not time1.year or not time2.year:
            return False
            
        if time1.year != time2.year:
            return False
            
        if time1.month and time2.month and time1.month != time2.month:
            return False
            
        if time1.day and time2.day and time1.day != time2.day:
            return False            
        return True


    def get_most_granular_time(self, time1: TimePoint, time2: TimePoint) -> TimePoint:
        """
        Returns the time point with more granular information
        """

        score1 = sum([bool(time1.year), bool(time1.month), bool(time1.day), bool(time1.time)])
        score2 = sum([bool(time2.year), bool(time2.month), bool(time2.day), bool(time2.time)])
        return time1 if score1 >= score2 else time2


    def compute_time_intersection(self, time1: TimePoint, time2: TimePoint) -> TimePoint:
        """
        Computes the intersection of two time points at their most precise common granularity
        """

        result = TimePoint(year=time1.year)
        
        if time1.month and time2.month and time1.month == time2.month:
            result.month = time1.month
            
            if time1.day and time2.day and time1.day == time2.day:
                result.day = time1.day
                
                if time1.time and time2.time and time1.time == time2.time:
                    result.time = time1.time
                    result.timezone = time1.timezone    
        return result
    

    def merge_rows(self, row1: Dict, row2: Dict, 
                  spatial_strategy: str = 'contained',
                  temporal_strategy: str = 'overlaps') -> Optional[Dict]:
        """
        Merges two rows based on their spatial and temporal attributes
        """

        # Check spatial match
        spatial_match = False
        merged_location = None
        
        if spatial_strategy == 'exact':
            spatial_match = row1['location'] == row2['location']
            merged_location = row1['location']
        elif spatial_strategy == 'contained':
            spatial_match = self.is_location_contained(row1['location'], row2['location'])
            merged_location = self.get_most_specific_location(row1['location'], row2['location'])
        elif spatial_strategy == 'nearest':
            spatial_match = self.find_nearest_point(row1['location'], row2['location'])
            merged_location = self.compute_weighted_location(row1['location'], row2['location'])
            
        if not spatial_match:
            return None
            
        # Check temporal match
        temporal_match = False
        merged_time = None
        
        if temporal_strategy == 'exact':
            temporal_match = row1['time'] == row2['time']
            merged_time = row1['time']
        elif temporal_strategy == 'overlaps':
            temporal_match = self.do_periods_overlap(row1['time'], row2['time'])
            merged_time = self.compute_time_intersection(row1['time'], row2['time'])
        elif temporal_strategy == 'contains':
            temporal_match = self.is_time_contained(row1['time'], row2['time'])
            merged_time = self.get_most_granular_time(row1['time'], row2['time'])
            
        if not temporal_match:
            return None
            
        # Merge the data
        merged_data = {**row1['data'], **row2['data']}
        
        return {
            'location': merged_location,
            'time': merged_time,
            'data': merged_data,
            'source_datasets': [row1['dataset_id'], row2['dataset_id']]
        }


    def merge_datasets(self, spatial_strategy: str = 'contained',
                      temporal_strategy: str = 'overlaps') -> List[Dict]:
        """
        Main function to merge two datasets
        """

        merged_rows = []
        
        # Create simple index for dataset2 rows
        indexed_rows2 = {}
        for row2 in self.dataset2.rows:
            key = f"{row2['location'].country}_{row2['time'].year}"
            if key not in indexed_rows2:
                indexed_rows2[key] = []
            indexed_rows2[key].append(row2)
            
        # Try to merge each row from dataset1
        for row1 in self.dataset1.rows:
            key = f"{row1['location'].country}_{row1['time'].year}"
            potential_matches = indexed_rows2.get(key, [])
            
            for row2 in potential_matches:
                merged_row = self.merge_rows(row1, row2, spatial_strategy, temporal_strategy)
                if merged_row:
                    merged_rows.append(merged_row)
        return merged_rows


    def distribute_to_smaller_timeframe(self, row: Dict, target_resolution: str) -> List[Dict]:
        """
        Distributes data from a larger timeframe to a smaller one
        """

        result = []
        time = row['time']
        
        if target_resolution == 'monthly' and not time.month:
            # Distribute yearly data to months
            for month in range(1, 13):
                new_time = TimePoint(
                    year=time.year,
                    month=month,
                    timezone=time.timezone
                )
                new_row = {**row, 'time': new_time}
                result.append(new_row)
                
        elif target_resolution == 'daily' and not time.day:
            # Distribute monthly data to days
            days_in_month = 30  # Simplified
            for day in range(1, days_in_month + 1):
                new_time = TimePoint(
                    year=time.year,
                    month=time.month,
                    day=day,
                    timezone=time.timezone
                )
                new_row = {**row, 'time': new_time}
                result.append(new_row)     
        return result


    def aggregate_timeframes(self, rows: List[Dict], target_resolution: str) -> List[Dict]:
        """
        Aggregates data from smaller timeframes to larger ones
        """

        aggregated = {}

        for row in rows:
            time = row['time']
            key = None
            
            if target_resolution == 'yearly':
                key = str(time.year)
            elif target_resolution == 'monthly':
                key = f"{time.year}_{time.month}"
                
            if key not in aggregated:
                aggregated[key] = []
            aggregated[key].append(row)
            
        result = []

        for key, rows in aggregated.items():
            # Simple averaging of numeric values
            merged_data = {}
            for row in rows:
                for field, value in row['data'].items():
                    if isinstance(value, (int, float)):
                        if field not in merged_data:
                            merged_data[field] = []
                        merged_data[field].append(value)
                        
            averaged_data = {
                field: sum(values) / len(values)
                for field, values in merged_data.items()
            }
            
            # Create aggregated row
            result.append({
                'location': rows[0]['location'],
                'time': TimePoint(year=rows[0]['time'].year),
                'data': averaged_data,
                'source_datasets': rows[0]['source_datasets']
            })
        return result
    
## TODO: Example use - write down as different scenarios in words
# merger = DatasetMerger(dataset1, dataset2)
# merged_rows = merger.merge_datasets()
# merged_rows = merger.merge_datasets(
#     spatial_strategy='nearest',
#     temporal_strategy='contains'
# )
# detailed_rows = merger.distribute_to_smaller_timeframe(row, 'monthly')
# summary_rows = merger.aggregate_timeframes(rows, 'yearly')
