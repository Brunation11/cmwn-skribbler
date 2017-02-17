# Skrambler - Node edition

The skrambler takes a skribble specification, creates a png, and uploads the image to s3.  This is designed to 
be used through AWS Lambda

## Deploying

Since the intention is too use this service with AWS lambda, automatic deploying is rather challenging.  Currently
the API sends a message to an SNS topic which then triggers the lambda function.  SNS is unable to point to a version 
of a lambda function at this time.  The main difficulty comes from SNS.  every deploy will need to modify subscripts 
(which is not allowed in SNS).  This means that a new subscription has to be added, the API pointer has to be updated, 
then the old subscription has to be deleted.  All these steps are un-reliable to verify.
 
Another challenge comes from the lambda environment.  In order for the skrambler to function, it needs to know which 
media, api and rollbar services to use.  This is currently a challenge that needs to be addressed in the API.

For the mean time, deploying will have to be a manual process following these steps:

1. Download the artifact you wish to use from S3 
1. Update the config.json and add to the zip package
1. Update the lambda function with the new zip package using the CLI or lambda console
    1. ```aws lambda update-function-code --function-name skramble_<env> --zip-file fileb://./<artifact>.zip```
1. Profit
