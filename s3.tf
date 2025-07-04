# s3.tf

# 1. Bucket para los videos originales subidos por los usuarios
resource "aws_s3_bucket" "original_videos" {
  bucket = "${lower(var.project_name)}-original-videos-${random_id.bucket_suffix.hex}"

  tags = {
    Name = "${var.project_name}-original-videos"
  }
}

resource "aws_s3_bucket_public_access_block" "original_videos_public_access_block" {
  bucket = aws_s3_bucket.original_videos.id

  block_public_acls   = true
  block_public_policy = true
  ignore_public_acls  = true
  restrict_public_buckets = true
}

# 2. Configuración de CORS para el bucket de videos originales
resource "aws_s3_bucket_cors_configuration" "original_videos_cors" {
  bucket = aws_s3_bucket.original_videos.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["PUT", "POST"]
    allowed_origins = ["*"] # En producción, se restringiría a la URL del frontend
    expose_headers  = ["ETag"]
  }
}

# 3. Bucket para los videos transcodificados
resource "aws_s3_bucket" "transcoded_videos" {
  bucket = "${lower(var.project_name)}-transcoded-videos-${random_id.bucket_suffix.hex}"

  tags = {
    Name = "${var.project_name}-transcoded-videos"
  }
}

resource "aws_s3_bucket_public_access_block" "transcoded_videos_public_access_block" {
  bucket = aws_s3_bucket.transcoded_videos.id

  block_public_acls   = true
  block_public_policy = true
  ignore_public_acls  = true
  restrict_public_buckets = true
}

# 4. Recurso para generar un sufijo aleatorio para los nombres de los buckets
# Esto evita errores si el nombre del bucket ya está en uso globalmente.
resource "random_id" "bucket_suffix" {
  byte_length = 8
}


