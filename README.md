# AWS CloudFormation tools
## generate.py3
`generate.py3` will consume yaml document, process it and output final json file. there are some custom function just like [aws cloud formation intrinsic function](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference.html)

usage:

    generate.py3 <main.yaml> [config.yaml]

available custom function:

 - `TVLK::Fn::FromFile`, parse single yaml file
 - `TVLK::Fn::FromFolders`, include all yaml file in a folder
 - `TVLK::Fn::FileAsBase64`, read file and represent it as base64 decoded string
 - `TVLK::Fn::GetConfig`, read value from `config.yaml`
 - `TVLK::Fn::Merge`, merge list of object into single object
 - `TVLK::Fn::Concat`, concat string

`config.yaml` is optional.

# TODO
- add more documentation, usage, how to, etc.

