from aws_cdk import Duration, RemovalPolicy, Stack
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_dynamodb as ddb
from aws_cdk import aws_lambda as _lambda
from constructs import Construct


class ApiServiceStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Defines an AWS DynamoDB resource
        table = ddb.Table(
            self,
            "Announcement",
            partition_key={"name": "title", "type": ddb.AttributeType.STRING},
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Defines an AWS Lambda resource
        my_lambda = _lambda.Function(
            self,
            "LambdaFunction",
            code=_lambda.Code.from_asset("lambda"),
            handler="lambda_function.handler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            environment={
                "LOG_LEVEL": "INFO",
                "TABLE_NAME": table.table_name,
                "DEFAULT_PAGINATION_SIZE": "5",
            },
            timeout=Duration.seconds(20),
        )

        # Grant DDB Read, Write permission to Lambda function
        table.grant_read_write_data(my_lambda)

        # Defines an AWS API Gateway resource
        api = apigw.LambdaRestApi(
            self,
            "ApiGateway",
            handler=my_lambda,
            proxy=False,
        )
        api.root.add_method("GET")
        items = api.root.add_resource("items")
        items.add_method("GET")
        items.add_method("POST")
