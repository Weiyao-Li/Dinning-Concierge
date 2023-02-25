import boto3
import sys
import json
import string
import requests
import datetime
from decimal import Decimal


AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''
tablen = 'yelp-restaurants'


def getdict(restaurant):
    businessID = restaurant['id']
    name = restaurant.get('name', '')
    address = restaurant.get('address','')
    latitude =  restaurant.get('latitude','')
    longitude = restaurant.get('longitude','')
    cuisine = restaurant.get('cuisine','')
    reviewCount = restaurant.get('review_count', 0)
    rating = int(restaurant.get('rating', 0))
    zipCode = restaurant.get('zip_code', None)
    insertedAtTimestamp = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S.%f")
    
    datadict = {
        'id': businessID,
        'cuisine': cuisine,
        'name': name,
        'address': address,
        'review_count': reviewCount,
        'rating': rating,
        'zip_code': zipCode,
        'latitude' : latitude,
        'longitude' : longitude,
        'inserted_at_timestamp': insertedAtTimestamp
    }

    
    return datadict



if __name__ == '__main__':
    print("Sending data to Dynamo DB")
    client = boto3.resource('dynamodb', region_name='us-east-1', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    table = client.Table(tablen)
    
    with open('modified_data.json', 'r') as f:
        restos = json.load(f,parse_float=Decimal)
        print("Total records for this cuisine",len(restos))    
        for index, restos in enumerate(restos):
            print("adding ",index)
            alladatadict = getdict(restos)
            table.put_item(Item=alladatadict)     




