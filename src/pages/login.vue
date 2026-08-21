<template>
  <v-container fluid class="fill-height">
    <v-row align="center" justify="center">
      <v-col cols="12" sm="6" md="5" lg="4" xl="3">
        <v-card elevation="12">
          <v-toolbar color="primary">
            <v-toolbar-title class="text-white">Log in</v-toolbar-title>
          </v-toolbar>

          <v-form ref="form" v-model="valid" @submit.prevent="submit">
            <v-card-text>
              <v-text-field
                v-model="username"
                autofocus
                prepend-inner-icon="mdi-account"
                name="username"
                label="Username"
                type="text"
                :rules="[rules.required]"
                :error-messages="errorMessages.username"
              ></v-text-field>
              <v-text-field
                v-model="password"
                prepend-inner-icon="mdi-lock"
                name="password"
                label="Password"
                type="password"
                :rules="[rules.required]"
                :error-messages="errorMessages.password"
              ></v-text-field>
            </v-card-text>

            <v-card-actions class="justify-center">
              <v-btn color="primary" type="submit">Log in</v-btn>
            </v-card-actions>
          </v-form>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";

import * as api from "@/api";
import { useAppStore } from "@/stores/app";

const router = useRouter();
const store = useAppStore();

const form = ref(null);
const valid = ref(false);
const username = ref("");
const password = ref("");
const rules = {
  required: (value) => !!value || "This field is required",
};
const errorMessages = ref({
  username: [],
  password: [],
});

async function submit() {
  const validation = await form.value.validate();
  if (!validation.valid) {
    return;
  }

  const formData = new FormData();
  formData.append("username", username.value);
  formData.append("password", password.value);

  const response = await api.login(formData);
  if (response.status === 200) {
    store.setIsAuthenticated(true);
    await store.init();
    await router.push({ path: "/group" });
    return;
  }

  const data = await response.json();
  errorMessages.value = data.errors ?? {
    username: [],
    password: [],
  };
}
</script>
