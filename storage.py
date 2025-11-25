import boto3
from boto3.dynamodb.conditions import Key


class DynamoDBStore:
    def __init__(
        self,
        table_name: str,
        region_name: str,
        part_key_name: str,
        sort_key_name: str,
        endpoint_url: str | None = None,
    ):
        self.table_name = table_name
        self.part_key_name = part_key_name
        self.sort_key_name = sort_key_name
        self.dynamodb = boto3.resource(
            "dynamodb", region_name=region_name, endpoint_url=endpoint_url
        )
        self.table = self.dynamodb.Table(table_name)

    def put_item(self, item: dict):
        self.table.put_item(Item=item)

    def get_item(self, pk: str, sk: str) -> dict | None:
        response = self.table.get_item(
            Key={self.part_key_name: pk, self.sort_key_name: sk}
        )
        return response.get("Item")

    def query_items(
        self, pk: str, sk_prefix: str | None = None, filters: dict | None = None
    ) -> list[dict]:
        key_condition = Key(self.part_key_name).eq(pk)
        if sk_prefix:
            key_condition = key_condition & Key(self.sort_key_name).begins_with(
                sk_prefix
            )

        query_kwargs = {"KeyConditionExpression": key_condition}

        if filters:
            filter_expression = " AND ".join(
                [f"{k} = :{k}" for k in filters.keys()]
            )
            expression_attribute_values = {
                f":{k}": v for k, v in filters.items()
            }
            query_kwargs["FilterExpression"] = filter_expression
            query_kwargs[
                "ExpressionAttributeValues"
            ] = expression_attribute_values

        response = self.table.query(**query_kwargs)
        return response.get("Items", [])

    def scan_by_pk_prefix(self, pk_prefix: str, sk: str) -> list[dict]:
        response = self.table.scan(
            FilterExpression=Key(self.part_key_name).begins_with(pk_prefix)
            & Key(self.sort_key_name).eq(sk)
        )
        return response.get("Items", [])

    def batch_put_items(self, items: list[dict]):
        with self.table.batch_writer() as batch:
            for item in items:
                batch.put_item(Item=item)
