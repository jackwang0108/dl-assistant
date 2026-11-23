# 工具库 (qrcode + iconify)

## qrcode.js（全局已引，二维码）
生成二维码，在幻灯片末尾分享链接或提供扫码入口。
```html
<div id="qrcode"></div>
<script>
  new QRCode(document.getElementById('qrcode'), {
    text: 'https://example.com',
    width: 200,
    height: 200,
    colorDark: '#000000',
    colorLight: '#ffffff'
  });
</script>
```

## iconify（按需引，海量图标）
Font Awesome 不够时用 iconify（含 Lucide/Tabler/Material/品牌 logo 等，百万图标，按需加载）：
```html
<script src="https://cdn.jsdelivr.net/npm/iconify-icon@2"></script>
<iconify-icon icon="lucide:rocket" width="32"></iconify-icon>
<iconify-icon icon="mdi:github" width="32"></iconify-icon>
```
图标名查 iconify.design。仅在使用这些图标的页面加载。
