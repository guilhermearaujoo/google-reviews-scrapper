import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
// import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as lambda from 'aws-cdk-lib/aws-lambda';

export class ArccaDockerLambdaStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
  
    const dockerFunction = new lambda.DockerImageFunction(this, 'DockerFunction', {
      code: lambda.DockerImageCode.fromImageAsset('./image'),
      memorySize: 1024,
      timeout: cdk.Duration.seconds(900),
      architecture: lambda.Architecture.X86_64,
    });

    const functionUrl = dockerFunction.addFunctionUrl({
      authType: lambda.FunctionUrlAuthType.NONE,
      cors: {
        allowedMethods: [lambda.HttpMethod.ALL],
        allowedHeaders: ['*'],
        allowedOrigins: ['*'],
      }
    });

    new cdk.CfnOutput(this, 'FunctionUrl', {
      value: functionUrl.url,
    });
  }
}
