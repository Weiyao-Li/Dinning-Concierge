import boto3
import sys
import json
import string
import requests
import datetime


CUISINES = ["indian", "italian", "ethiopian", "american", "mexican", "japanese", "french","spanish","chinese"]


AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''
tablen = 'yelp-restaurants'


def getaddress(restaurant):
    return str(" ".join(restaurant['location'].get('display_address', [])))

def getdict(restaurant):
    businessID = restaurant['id']
    name = restaurant.get('name', '')
    address = getaddress(restaurant)
    latitude =  restaurant['coordinates'].get('latitude')
    longitude = restaurant['coordinates'].get('longitude')
    # cuisine = restaurant['cuisine']
    reviewCount = restaurant.get('review_count', 0)
    rating = int(restaurant.get('rating', 0))
    zipCode = restaurant['location'].get('zip_code', None)
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
        'longitude' : longitude
        'inserted_at_timestamp': insertedAtTimestamp
    }

    
    return datadict



if __name__ == '__main__':
    print("Sending data to Dynamo DB")
    client = boto3.resource('dynamodb', region_name='us-east-1', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    table = client.Table(tablen)
    
    for c in CUISINES:
        with open('./restaurants/{}_data.json'.format(c), 'r') as f:
            restos = json.load(f)
            print("Putting in Dynamo for ",c)
            print("Total records for this cuisine",len(restos))    
            for index, restos in enumerate(restos):
                print("adding ",index)
                alladatadict = getdict(restos, c)
                table.put_item(Item=alladatadict)     




