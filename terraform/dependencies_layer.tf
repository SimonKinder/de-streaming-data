data "archive_file" "dependecies_layer" {
  type        = "zip"
  output_path = "${path.module}/../packages/layer/httpx_layer.zip"
  source_dir  = "${path.module}/../dependencies"
}

resource "aws_lambda_layer_version" "dependencies" {
  layer_name = "httpx_layer"
  filename = data.archive_file.dependecies_layer.output_path
  source_code_hash = data.archive_file.dependecies_layer.output_base64sha256
  compatible_runtimes = [ "python3.12" ]
  }