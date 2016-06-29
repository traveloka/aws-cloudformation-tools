# AWS CloudFormation tools
## generate.py
`generate.py` will consume yaml document, process it and output final json file. there are some custom function just like [aws cloud formation intrinsic function](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference.html)

usage:

    generate.py <main.yaml> [-c config.yaml] [-o output.json] [-r retry_count]

available custom function:

- `TVLK::FromFile`, parse single yaml file
- `TVLK::FromFolder`, include all yaml file in a folder
- `TVLK::Base64OfFile`, read file and represent it as base64 decoded string
- `TVLK::Base64OfMakefileTarget`, run `make target` and read target file and represent it as base64 decoded string
- `TVLK::Config`, read value from `config.yaml`
- `TVLK::Merge`, merge list of object into single object
- `TVLK::MergeList`, merge list of list into single list
- `TVLK::Concat`, concat string
- `TVLK::If`,
- `TVLK::Equals`,
- `TVLK::And`,
- `TVLK::Or`,
- `TVLK::Not`,
- `TVLK::CFStackResource`, get physical id of existing CloudFormation stack resource
- `TVLK::EC2PublicIp`, get public ip of existing EC2 instance
- `TVLK::EC2PrivateIp`, get private ip of existing EC2 instance

# TODO
- add more documentation, usage, how to, etc.

