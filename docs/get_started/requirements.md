#### Python version required: 3.10+

#### Docker

Visit the official docker website 🐋 at this <a href="https://docs.docker.com/engine/install/" target="_blank">link</a> on how to install on your system.

#### AWS Credentials

You will need to create a new user in AWS IAM and get the following:

- Access Key ID
- Secret Access Key
- Region
- Account ID

For development purposes use the following policy on your AWS user. For <u>production</u> always use <u>the least privilege principle</u> when creating policies or <u>use more secure methods</u>. (<a href="https://docs.aws.amazon.com/IAM/latest/UserGuide/security.html", target="\_blank">See</a>)<br>

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["sts:AssumeRole"],
      "Resource": ["arn:aws:iam::*:role/cdk-*"]
    },
    {
      "Effect": "Allow",
      "Action": ["iot:Connect", "iot:DescribeEndpoint"],
      "Resource": ["*"]
    },
    {
      "Effect": "Allow",
      "Action": ["iot:Publish", "iot:Receive"],
      "Resource": "arn:aws:iot:*:*:topic/fluxional*"
    },
    {
      "Effect": "Allow",
      "Action": "iot:Subscribe",
      "Resource": "arn:aws:iot:*:*:topicfilter/fluxional*"
    }
  ]
}
```
