package com.magna.controltower.adapter;

import android.content.Context;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.cardview.widget.CardView;
import androidx.recyclerview.widget.RecyclerView;

import com.magna.controltower.R;
import com.magna.controltower.model.KasaItem;

import java.util.List;

public class KasaAdapter extends RecyclerView.Adapter<KasaAdapter.VH> {

    private static final String TAG = "KasaAdapter";
    private final Context ctx;
    private List<KasaItem> data;
    private final String loadingSessionId;

    public KasaAdapter(Context ctx, List<KasaItem> data, String loadingSessionId) {
        this.ctx = ctx;
        this.data = data;
        this.loadingSessionId = loadingSessionId;
    }

    public void updateData(List<KasaItem> newData) {
        // Preserve expand states from old data
        if (this.data != null && !this.data.isEmpty()) {
            for (KasaItem oldItem : this.data) {
                for (KasaItem newItem : newData) {
                    if (oldItem.getKasaNo().equals(newItem.getKasaNo())) {
                        // Preserve expanded state
                        newItem.setExpanded(oldItem.isExpanded());
                        break;
                    }
                }
            }
        }

        this.data = newData;
        notifyDataSetChanged();
    }

    public List<KasaItem> getData() {
        return data;
    }

    @NonNull
    @Override
    public VH onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View v = LayoutInflater.from(ctx).inflate(R.layout.item_kasa_row, parent, false);
        return new VH(v);
    }

    @Override
    public void onBindViewHolder(@NonNull VH h, int pos) {
        KasaItem item = data.get(pos);

        // 🔍 DEBUG: KasaItem içindeki dolly_order_no değerini kontrol et
        String orderNo = item.getDollyOrderNo();
        Log.d(TAG, "🎯 Binding pos=" + pos + ", kasaNo=" + item.getKasaNo() + 
                   ", getDollyOrderNo()='" + orderNo + "' (null? " + (orderNo == null) + 
                   ", empty? " + (orderNo != null && orderNo.isEmpty()) + ")");

        // Order No (büyük) ve Dolly No (küçük)
        h.tvKasaNo.setText(item.getDollyOrderNo() != null ? item.getDollyOrderNo() : "SEQ-???");
        h.tvDollyNo.setText("Dolly: " + item.getKasaNo());
        h.tvFirstVin.setText("İlk VIN: " + item.getFirstVin());
        h.tvLastVin.setText("Son VIN: " + item.getLastVin());

        Log.d(TAG, "Binding item " + pos + ": " + item.getKasaNo() + 
                   " (Order: " + item.getDollyOrderNo() + ")" +
                   ", VIN count: " + item.getVinList().size() + 
                   ", Expanded: " + item.isExpanded());

        // Arka planı duruma göre boya (kart komple)
        CardView card = (CardView) h.itemView;
        switch (item.getStatus()) {
            case SCANNED:
                card.setCardBackgroundColor(h.itemView.getResources().getColor(R.color.row_scanned));
                break;
            case SKIPPED:
                card.setCardBackgroundColor(h.itemView.getResources().getColor(R.color.row_skipped));
                break;
            default:
                card.setCardBackgroundColor(h.itemView.getResources().getColor(R.color.row_pending));
        }

        // Expand alanını doldur
        h.expandArea.removeAllViews();
        if (item.isExpanded()) {
            h.expandArea.setVisibility(View.VISIBLE);
            Log.d(TAG, "Expanding item " + item.getKasaNo() + " with " + item.getVinList().size() + " VINs");
            
            // VIN'leri ekle
            for (String vin : item.getVinList()) {
                TextView tv = new TextView(ctx);
                tv.setText("• " + vin);
                tv.setTextColor(0xFFCDD8E6);
                tv.setTextSize(14);
                tv.setPadding(0, 6, 0, 6);
                h.expandArea.addView(tv);
                Log.d(TAG, "  Added VIN: " + vin);
            }
        } else {
            h.expandArea.setVisibility(View.GONE);
        }

        // Tıklama: toggle expand/collapse
        h.itemView.setOnClickListener(v -> {
            boolean newState = !item.isExpanded();
            Log.d(TAG, "Clicked item " + item.getKasaNo() + ", expanding: " + newState);
            item.setExpanded(newState);
            notifyItemChanged(pos);
        });
    }

    @Override
    public int getItemCount() {
        return data.size();
    }

    static class VH extends RecyclerView.ViewHolder {
        TextView tvKasaNo, tvDollyNo, tvFirstVin, tvLastVin;
        LinearLayout expandArea;

        VH(@NonNull View itemView) {
            super(itemView);
            tvKasaNo = itemView.findViewById(R.id.tvKasaNo);
            tvDollyNo = itemView.findViewById(R.id.tvDollyNo);
            tvFirstVin = itemView.findViewById(R.id.tvFirstVin);
            tvLastVin = itemView.findViewById(R.id.tvLastVin);
            expandArea = itemView.findViewById(R.id.expandArea);
        }
    }
}
