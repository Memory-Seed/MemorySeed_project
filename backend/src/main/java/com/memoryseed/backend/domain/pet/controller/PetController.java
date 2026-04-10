package com.memoryseed.backend.domain.pet.controller;

import com.memoryseed.backend.domain.pet.dto.CustomizationRequest;
import com.memoryseed.backend.domain.pet.dto.PetResponse;
import com.memoryseed.backend.domain.pet.service.PetService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/pet")
public class PetController {

    private final PetService petService;

    public PetController(PetService petService) {
        this.petService = petService;
    }

    @GetMapping
    public ResponseEntity<PetResponse> getPet(
            Authentication authentication
    ) {
        String providerId = authentication.getName();
        return ResponseEntity.ok(petService.getPet(providerId));
    }

    @PutMapping("/customization")
    public ResponseEntity<PetResponse> apply(
            Authentication authentication,
            @RequestBody CustomizationRequest req
    ) {
        String providerId = authentication.getName();
        return ResponseEntity.ok(petService.applyCustomization(providerId, req));
    }
}