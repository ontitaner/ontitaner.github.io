/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  images: { unoptimized: true },
  // 如果部署到 https://<user>.github.io/<repo>/，取消下面注释并填写 repo 名
  // basePath: '/<repo-name>',
  // assetPrefix: '/<repo-name>/',
};

export default nextConfig;
