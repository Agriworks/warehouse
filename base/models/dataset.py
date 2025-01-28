
from mongoengine import DynamicDocument, StringField, ReferenceField, ListField, IntField, DateTimeField, BooleanField, DictField, EmbeddedDocumentField
from datetime import datetime
from mongoengine.queryset.visitor import Q
from models.user import User
from models.location import LocationHierarchy, LocationSpan
from models.time import TimeSpan, TimePoint

class Dataset(DynamicDocument):
    """
    Represents a dataset uploaded by a user
    """

    # Unique identifier for a dataset
    dataset_id = IntField(required=True)

    # Title of dataset
    title = StringField(required=True)

    # Description of dataset
    description = StringField()

    # The creator of the dataset
    author = ReferenceField(User, required=True)

    # Date of creation of dataset
    date_created = DateTimeField()

    ## TODO: abstract out metadata into a separate model when we iterate for user permissions
    # When the dataset was uploaded
    upload_date = DateTimeField(default=datetime.now())

    # User friendly column names
    legend = DictField(required=False)

    # Ground truth column labels
    column_labels = ListField(required=True)

    # Is it available for public view
    is_public = BooleanField(required=True)

    # Semantic keywords to describe the data
    tags = ListField()

    # Spatial information
    locations = ListField(EmbeddedDocumentField(LocationHierarchy))
    location_span = EmbeddedDocumentField(LocationSpan)
    
    # Temporal information
    timepoints = ListField(EmbeddedDocumentField(TimePoint))
    time_span = EmbeddedDocumentField(TimeSpan)

    # TODO: Index keys
    # keys = Field(required=True)

    # Search indexing
    meta = {
        'indexes': [
            {
                'fields': [
                    '$title', 
                    '$tags',
                    'locations.country',
                    'locations.state',
                    'locations.district',
                    'timepoints.year'
                ],
                'weights': {
                    'title': 5,
                    'tags': 3,
                    'locations.country': 2,
                    'timepoints.year': 2
                }
            }
        ]
    }

class DataRows(DynamicDocument):

    ## TODO: Add compund indexes for common queries
    dataset_id = IntField(required=True)
    
    meta = {
        'indexes': [
            {'fields': ['dataset_id']},
        ],
        'auto_create_index': True
    }



class DataRows(DynamicDocument):
    """Helps partition huge datasets and perform bulk operations"""
    
    dataset_id = IntField(required=True)
    partition_key = StringField(required=True)  
    # Partition key syntax eg "2024_01"
    
    @classmethod
    def get_partition_key(cls, date):
        return f"{date.year}_{date.month:02d}"

    def bulk_insert_rows(dataset_id, rows):
        batch_size = 1000
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            DataRows.objects.insert(batch)

    def bulk_query_dataset(dataset_id, filters=None):
        base_q = Q(dataset_id=dataset_id)
        if filters:
            base_q = base_q & filters
        
        return DataRows.objects(base_q).batch_size(1000)
