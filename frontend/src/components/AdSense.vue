<!-- AdSense.vue -->
<template>
    <div class="ad-container">
        <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-7892198097991803"
            data-ad-slot="7818434784" data-ad-format="auto" data-full-width-responsive="true"></ins>
    </div>
</template>

<script>
export default {
    name: 'AdSense',
    mounted() {
        (window.adsbygoogle = window.adsbygoogle || []).push({});
    }
}
</script>

<style scoped>
.ad-container {
    width: 100%;
    margin: 20px 0;
}
</style>