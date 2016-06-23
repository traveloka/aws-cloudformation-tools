# AWS CloudFormation tools
## generate.py
`generate.py3` will consume yaml document, process it and output final json file. there are some custom function just like [aws cloud formation intrinsic function](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference.html)

usage:

    generate.py <main.yaml> [-c config.yaml] [-o output.json]

available custom function:

 - `TVLK::FromFile`, parse single yaml file
 - `TVLK::FromFolders`, include all yaml file in a folder
 - `TVLK::FileAsBase64`, read file and represent it as base64 decoded string
 - `TVLK::GetConfig`, read value from `config.yaml`
 - `TVLK::Merge`, merge list of object into single object
 - `TVLK::MergeList`, merge list of list into single list
 - `TVLK::Concat`, concat string
 - `TVLK::MakefileAsBase64`, run `make target` and read target file and represent it as base64 decoded string
 - `TVLK::If`
 - `TVLK::Equals`
 - `TVLK::And`
 - `TVLK::Or`
 - `TVLK::Not`
 - `TVLK::AWSCFGetStackResource`, get physical id of other cloudformation stack resource

`config.yaml` is optional.

# TODO
- add more documentation, usage, how to, etc.

