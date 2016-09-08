# AWS CloudFormation tools
## generate
`generate` will consume yaml document, process it and output final json file. there are some custom function just like [aws cloud formation intrinsic function](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference.html)

usage:

    generate.py <main.yaml> [-c config.yaml] [-o output.json] [-r retry_count]

available custom function:

- `TVLK::FromFile`, parse single yaml file
- `TVLK::FromFolder`, include all yaml file in a folder
- `TVLK::Base64`, convert string to base64 of it
- `TVLK::ReadTextFile`, read text from file, file must be encoded in utf8
- `TVLK::Base64OfFile`, read file and represent it as base64 decoded string
- `TVLK::RunCommand`, invoke command and capture stdout of it, must be encoded in utf8
- `TVLK::Config`, read value from config file
- `TVLK::Merge`, merge list of object into single object
- `TVLK::MergeList`, merge list of list into single list
- `TVLK::Concat`, concat string
- `TVLK::If`,
- `TVLK::Equals`,
- `TVLK::And`,
- `TVLK::Or`,
- `TVLK::Not`,
- `TVLK::Select`

# TODO
- add more documentation, usage, how to, etc.

