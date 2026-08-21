<template lang="html">
  <v-chip
    label
    variant="flat"
    :color="stateColorMap[state]"
    class="text-white"
    :small="small"
  >
    {{ state }}
  </v-chip>
</template>

<script setup>
import { stateColorMap } from "@/multivisor";

//const props = defineProps(['state', 'small'])

const { state, small } = defineProps({
  state: { default: "UNKNOWN" },
  small: { default: false },
});
</script>
