/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  // API 프록시: src/app/api/v1/**/route.ts (backend-proxy.ts) 사용
  // next.config rewrites 와 중복하면 404/라우팅 충돌 가능 → 사용하지 않음
};

module.exports = nextConfig;
