<template>
  <v-container fluid>
    <v-data-iterator
      item-key="name"
      :items="filteredGroups"
      no-results-text="Sorry, no matching processes found"
      no-data-text="Sorry, there are no processes currently being monitored"
    >
      <MasonryWall
        :items="filteredGroups"
        :column-width="360"
        :gap="12"
        :max-columns="3"
        :ssr-columns="1"
        :key-mapper="groupKey"
      >
        <template #default="{ item: group }">
          <GroupCard :group="group"></GroupCard>
        </template>
      </MasonryWall>
    </v-data-iterator>
  </v-container>
</template>

<script setup>
import GroupCard from "@/components/group/Card";
import { MasonryWall } from "@yeger/vue-masonry-wall";

import { useAppStore } from "@/stores/app";

const store = useAppStore();

const groupKey = (group) => group.name;

const { filteredGroups } = storeToRefs(store);
</script>
