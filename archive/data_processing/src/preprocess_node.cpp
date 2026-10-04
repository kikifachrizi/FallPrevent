// preprocess_node.cpp

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/float32_multi_array.hpp>

#include <vector>
#include <deque>
#include <cmath>
#include <algorithm>

using std::placeholders::_1;

#define HEIGHT 180
#define WIDTH 240
#define RESIZE 64
#define SEQ_LEN 90

class PreprocessNode : public rclcpp::Node
{
public:
    PreprocessNode() : Node("preprocess_node")
    {
        sub_ = this->create_subscription<std_msgs::msg::Float32MultiArray>(
            "/depth_frame", 50,
            std::bind(&PreprocessNode::callback, this, _1));

        pub_ = this->create_publisher<std_msgs::msg::Float32MultiArray>(
            "/processed_sequence", 10);

        RCLCPP_INFO(this->get_logger(), "Preprocess Node Ready");
    }

private:
    rclcpp::Subscription<std_msgs::msg::Float32MultiArray>::SharedPtr sub_;
    rclcpp::Publisher<std_msgs::msg::Float32MultiArray>::SharedPtr pub_;

    std::deque<std::vector<float>> buffer_;

    float clamp(float v, float min_val, float max_val)
    {
        return std::max(min_val, std::min(v, max_val));
    }

    std::vector<float> resize_frame(const std::vector<float>& frame)
    {
        std::vector<float> out(RESIZE * RESIZE);

        for (int y = 0; y < RESIZE; y++)
        {
            for (int x = 0; x < RESIZE; x++)
            {
                int src_y = y * HEIGHT / RESIZE;
                int src_x = x * WIDTH / RESIZE;

                out[y * RESIZE + x] = frame[src_y * WIDTH + src_x];
            }
        }
        return out;
    }

    void callback(const std_msgs::msg::Float32MultiArray::SharedPtr msg)
    {
        std::vector<float> frame = msg->data;

        // preprocess per frame
        for (auto &v : frame)
        {
            if (std::isnan(v)) v = 0;
            v = clamp(v, 100, 4000);
            v = v / 4000.0;
        }

        buffer_.push_back(frame);

        if (buffer_.size() >= SEQ_LEN)
        {
            std::vector<float> output;

            // differencing
            for (int i = 1; i < buffer_.size(); i++)
            {
                std::vector<float> diff(HEIGHT * WIDTH);

                for (int j = 0; j < HEIGHT * WIDTH; j++)
                {
                    diff[j] = buffer_[i][j] - buffer_[i - 1][j];
                }

                // resize
                diff = resize_frame(diff);

                output.insert(output.end(), diff.begin(), diff.end());
            }

            std_msgs::msg::Float32MultiArray out_msg;
            out_msg.data = output;

            pub_->publish(out_msg);

            buffer_.clear(); // reset
        }
    }
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<PreprocessNode>());
    rclcpp::shutdown();
    return 0;
}