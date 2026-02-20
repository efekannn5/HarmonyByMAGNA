package com.magna.controltower.api;

import com.magna.controltower.api.models.*;

import java.util.List;

import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.GET;
import retrofit2.http.POST;
import retrofit2.http.Path;

/**
 * Harmony Ecosystem Forklift API Service
 * Base URL: http://10.25.64.181:8181/api
 */
public interface ForkliftApiService {

        // ============ Authentication ============

        /**
         * Login operator with barcode
         * POST /api/forklift/login
         */
        @POST("forklift/login")
        Call<LoginResponse> login(@Body LoginRequest request);

        /**
         * Logout current session
         * POST /api/forklift/logout
         */
        @POST("forklift/logout")
        Call<Void> logout();

        // ============ Dolly Status (Dolma Durumu) ============

        /**
         * Get EOL dolly filling status
         * GET /api/yuzde
         */
        @GET("yuzde")
        Call<EOLStatusResponse> getEOLStatus();

        // ============ Forklift Operations (Dolly Yükleme) ============

        /**
         * Scan dolly barcode for loading
         * POST /api/forklift/scan
         */
        @POST("forklift/scan")
        Call<DollyHoldEntry> scanDolly(
                        @Body ScanDollyRequest request);

        /**
         * Remove last scanned dolly (LIFO)
         * POST /api/forklift/remove-last
         */
        @POST("forklift/remove-last")
        Call<DollyHoldEntry> removeLastDolly(
                        @Body RemoveLastRequest request);

        /**
         * Complete loading session
         * POST /api/forklift/complete-loading
         */
        @POST("forklift/complete-loading")
        Call<CompleteLoadingResponse> completeLoading(
                        @Body CompleteLoadingRequest request);

        // ============ Manual Collection (Manuel Toplama) ============

        /**
         * Get list of groups with their EOLs for manual collection
         * GET /api/manual-collection/groups
         */
        @GET("manual-collection/groups")
        Call<List<ManualCollectionGroup>> getManualCollectionGroups();

        /**
         * Get dollys for a specific EOL within a group
         * GET /api/manual-collection/groups/{groupId}/eols/{eolId}
         */
        @GET("manual-collection/groups/{groupId}/eols/{eolId}")
        Call<EOLDollysResponse> getEOLDollys(
                        @Path("groupId") int groupId,
                        @Path("eolId") int eolId);

        /**
         * Get all EOLs and their dollys for a specific group
         * GET /api/manual-collection/groups/{groupId}
         */
        @GET("manual-collection/groups/{groupId}")
        Call<GroupDollysResponse> getGroupDollys(
                        @Path("groupId") int groupId);

        /**
         * Scan dolly for manual collection
         * POST /api/manual-collection/scan
         */
        @POST("manual-collection/scan")
        Call<ManualScanResponse> manualScan(
                        @Body ManualScanRequest request);

        /**
         * Remove last scanned dolly from manual collection
         * POST /api/manual-collection/remove-last
         */
        @POST("manual-collection/remove-last")
        Call<ManualScanResponse> manualRemoveLast(
                        @Body ManualScanRequest request);

        /**
         * Submit/complete manual collection from mobile (Android)
         * POST /api/manual-collection/mobile-submit
         */
        @POST("manual-collection/mobile-submit")
        Call<ManualSubmitResponse> manualSubmit(
                        @Body ManualSubmitRequest request);

        // ============ Telemetry (Movement + Location) ============

        /**
         * Upload telemetry batch
         * POST /api/forklift/telemetry
         */
        @POST("forklift/telemetry")
        Call<ForkliftTelemetryResponse> sendTelemetry(
                        @Body ForkliftTelemetryRequest request);
}
