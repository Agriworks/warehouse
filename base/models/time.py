from mongoengine import EmbeddedDocument, StringField, DateTimeField, IntField, BooleanField, EmbeddedDocumentField, ListField
from datetime import datetime


class TimePoint(EmbeddedDocument):
    """
    Represents a specific point in time
    """

    year = IntField(required=True)
    month = IntField(min_value=1, max_value=12)
    day = IntField(min_value=1, max_value=31)
    time = DateTimeField()
    ## TODO: timezone = StringField(default='UTC')
    # use standard timezone format
    
    def to_datetime(self) -> datetime:
        """
        Converts the TimePoint to a datetime object
        """

        if self.time:
            return self.time
        
        # Build datetime from components
        components = {
            'year': self.year,
            'month': self.month or 1,
            'day': self.day or 1
        }
        return datetime(**components)
    
    ## TODO: Validation needs to be added
    def validate(self):
        """Validates the time point"""
    
        if self.month and not self.year:
            raise ValueError("Cannot specify month without year")
        if self.day and not self.month:
            raise ValueError("Cannot specify day without month")
        if self.time and not self.timezone:
            raise ValueError("Timezone must be specified when time is provided")

class TimeSpan(EmbeddedDocument):
    """
    Represents a time span with various granularity levels
    """

    start = EmbeddedDocumentField(TimePoint, required=True)
    end = EmbeddedDocumentField(TimePoint, required=True)
    
    # Granularity of the data
    resolution = StringField(choices=['yearly', 'monthly', 'daily', 'hourly', 'mixed'], required=True)
    
    ## TODO: For irregular time series - expand on this - how do we handle missing data?
    has_gaps = BooleanField(default=False)
    gap_description = StringField()
    
    ## TODO: Validation needed 1-12 months, 1-31 days
    # Time span properties
    unique_years = ListField(IntField())
    unique_months = ListField(IntField())
    unique_days = ListField(IntField())
    
    def validate(self):
        """Validates the time span"""

        if self.start.to_datetime() > self.end.to_datetime():
            raise ValueError("Start time must be before end time")
    
    def add_timepoint(self, timepoint: TimePoint):
        """Updates span information based on a new timepoint"""

        if timepoint.year not in self.unique_years:
            self.unique_years.append(timepoint.year)
            self.unique_years.sort()
        
        if timepoint.month and timepoint.month not in self.unique_months:
            self.unique_months.append(timepoint.month)
            self.unique_months.sort()
            
        if timepoint.day and timepoint.day not in self.unique_days:
            self.unique_days.append(timepoint.day)
            self.unique_days.sort()
